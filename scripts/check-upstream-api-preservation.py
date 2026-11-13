#!/usr/bin/env python3
"""Fail early if NabdhGram overlays erase Telegram Java APIs.

Compares the pinned, immutable Telegram HEAD tree with generated Java *after*
all overlays. This is a source-compatibility gate, not a substitute for
Gradle compilation or real-device regression tests.
"""
from collections import Counter
from pathlib import Path
import re
import subprocess
import sys

# Native components frequently modified by the NabdhGram design, login,
# sessions or launcher overlays. Review this set on each upstream upgrade.
CRITICAL_FILES = (
    "ActionBar/MessageDrawable.java",
    "Cells/AppIconsSelectorCell.java",
    "Cells/SessionCell.java",
    "Components/ChatActivityEnterView.java",
    "Components/CustomPhoneKeyboardView.java",
    "Components/OutlineTextContainerView.java",
    "Components/UniversalAdapter.java",
    "ConnectionsManager.java",  # Resolved below to tgnet/.
    "ContactsActivity.java",
    "DefaultThemesPreviewCell.java",
    "LauncherIconController.java",
    "LoginActivity.java",
    "SessionBottomSheet.java",
    "SettingsActivity.java",
    "ThemeActivity.java",
)

JAVA = Path("TMessagesProj/src/main/java/org/telegram")
# Matches explicitly declared methods. The body may change, but a method
# should not disappear accidentally as a side effect of a substring splice.
METHOD = re.compile(
    r"(?m)^[ \t]*(?:(?:public|protected|private|static|final|"
    r"synchronized|abstract|native|default|strictfp)[ \t]+){1,8}"
    r"(?:<[^(){};\n]+>[ \t]+)?"
    r"[A-Za-z_$][\w.$<>?,\[\] \t]*[ \t]+"
    r"(?P<name>[A-Za-z_$][\w$]*)[ \t]*\("
)

def mask_noncode(source):
    """Mask comments and literals without altering line breaks/positions."""
    out = list(source)
    mode = "code"
    i = 0
    while i < len(source):
        c = source[i]
        nxt = source[i:i + 3]
        two = source[i:i + 2]
        if mode == "code":
            if two == "//":
                mode = "line"
                out[i] = out[i + 1] = " "
                i += 2
                continue
            if two == "/*":
                mode = "block"
                out[i] = out[i + 1] = " "
                i += 2
                continue
            if nxt == '"""':
                mode = "triple"
                out[i:i + 3] = [" ", " ", " "]
                i += 3
                continue
            if c in ('"', "'"):
                mode = c
                out[i] = " "
        elif mode == "line":
            if c == "\n":
                mode = "code"
            else:
                out[i] = " "
        elif mode == "block":
            if two == "*/":
                out[i] = out[i + 1] = " "
                mode = "code"
                i += 2
                continue
            if c != "\n":
                out[i] = " "
        elif mode == "triple":
            if nxt == '"""':
                out[i:i + 3] = [" ", " ", " "]
                mode = "code"
                i += 3
                continue
            if c != "\n":
                out[i] = " "
        else:
            if c == "\\":
                out[i] = " "
                if i + 1 < len(source):
                    if source[i + 1] != "\n":
                        out[i + 1] = " "
                    i += 2
                    continue
            elif c == mode:
                mode = "code"
            if c != "\n":
                out[i] = " "
        i += 1
    return "".join(out)

def syntax_delimiters_ok(code):
    # Catch unbalanced Java expression/block delimiters before spending time
    # initializing the native toolchain. Do not parse symbols inside strings.
    stack = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for char in mask_noncode(code):
        if char in "([{":
            stack.append(char)
        elif char in ")]}":
            if not stack or stack.pop() != pairs[char]:
                return False
    return not stack

def declared_methods(code):
    # Count rather than just set: an erased overload with another declaration
    # of the same name must still be reported.
    return Counter(m.group("name") for m in METHOD.finditer(mask_noncode(code)))

# The original 15 critical files remain mandatory even if an overlay does
# not touch them. Every other tracked Java file edited by an overlay is also
# checked, eliminating the previous blind spot for newer Telegram classes.
def modified_native_files(root):
    prefix = JAVA.as_posix()
    changed = subprocess.run(
        ["git", "-C", str(root), "diff", "--name-only", "--diff-filter=ACDMRT",
         "HEAD", "--", prefix],
        capture_output=True, text=True, check=True, encoding="utf-8"
    ).stdout
    added = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard",
         "--", prefix],
        capture_output=True, text=True, check=True, encoding="utf-8"
    ).stdout
    changed_paths = {Path(line) for line in changed.splitlines()
                     if line.endswith(".java")}
    added_paths = {Path(line) for line in added.splitlines()
                   if line.endswith(".java")}
    return changed_paths, added_paths


# Comparing names alone misses an erased overload when a different overload
# has the same name. Count method-name + argument arity, ignoring commas inside
# generic type arguments and annotations. This is deliberately a conservative
# *preflight*, not a complete Java AST parser; javac is still mandatory.
def declared_method_arities(code):
    masked = mask_noncode(code)
    found = Counter()
    for method in METHOD.finditer(masked):
        parens = 1
        angles = 0
        braces = 0
        brackets = 0
        arity = 0
        parameter = False
        for char in masked[method.end():]:
            if char == "(":
                parens += 1
            elif char == ")":
                parens -= 1
                if parens == 0:
                    if parameter:
                        arity += 1
                    found[(method.group("name"), arity)] += 1
                    break
            elif parens == 1:
                if char == "<":
                    angles += 1
                elif char == ">" and angles:
                    angles -= 1
                elif char == "{":
                    braces += 1
                elif char == "}" and braces:
                    braces -= 1
                elif char == "[":
                    brackets += 1
                elif char == "]" and brackets:
                    brackets -= 1
                elif char == "," and not (angles or braces or brackets):
                    arity += 1
                    parameter = False
                    continue
            if parens == 1 and not char.isspace():
                parameter = True
        else:
            raise ValueError("Unclosed Java method declaration: " + method.group("name"))
    return found


JAVA_TYPE = re.compile(r"\b(?P<kind>class|interface|enum|record)\s+"
                       r"(?P<name>[A-Za-z_$][\w$]*)\b")


def declared_types(code):
    return Counter((match.group("kind"), match.group("name"))
                   for match in JAVA_TYPE.finditer(mask_noncode(code)))


def path_for(name):
    if name == "ConnectionsManager.java":
        return JAVA / "tgnet" / name
    return JAVA / "ui" / name

def baseline(root, relative):
    p = subprocess.run(
        ["git", "-C", str(root), "show", "HEAD:" + relative.as_posix()],
        capture_output=True, text=True, check=True, encoding="utf-8"
    )
    return p.stdout

def assert_compatible(root):
    failures = []
    changed, added = modified_native_files(root)
    protected = {path_for(name) for name in CRITICAL_FILES} | changed
    missing_files = 0
    checked_methods = 0
    for relative in sorted(protected):
        generated_file = root / relative
        if not generated_file.is_file():
            failures.append(str(relative) + ": upstream Java file removed by overlays")
            missing_files += 1
            continue
        original = baseline(root, relative)
        generated = generated_file.read_text(encoding="utf-8")
        if not syntax_delimiters_ok(generated):
            failures.append(str(relative) + ": unbalanced Java delimiters after overlays")
        # Name-only counts are kept as a useful diagnostic while overload arity
        # checks catch a second failure mode (replaced same-name declarations).
        names_before, names_after = declared_methods(original), declared_methods(generated)
        lost_names = names_before - names_after
        if lost_names:
            failures.append(
                str(relative) + ": erased native Java method(s): "
                + ", ".join(f"{name} (x{count})"
                            for name, count in sorted(lost_names.items()))
            )
        try:
            arities_before = declared_method_arities(original)
            arities_after = declared_method_arities(generated)
        except ValueError as error:
            failures.append(str(relative) + ": " + str(error))
            continue
        checked_methods += sum(arities_before.values())
        lost_overloads = arities_before - arities_after
        if lost_overloads:
            failures.append(
                str(relative) + ": erased native Java overload(s): "
                + ", ".join(f"{name}/{arity} (x{count})"
                            for (name, arity), count in sorted(lost_overloads.items()))
            )
        lost_types = declared_types(original) - declared_types(generated)
        if lost_types:
            failures.append(
                str(relative) + ": erased native Java type(s): "
                + ", ".join(f"{kind} {name} (x{count})"
                            for (kind, name), count in sorted(lost_types.items()))
            )
        if not (lost_names or lost_overloads or lost_types):
            print(f"PASS: preserved {sum(arities_before.values())} Java method "
                  f"declarations and native types: {relative}")

    for relative in sorted(added):
        # Generated helper classes have no original upstream baseline; guard
        # their structural syntax before the expensive Java compiler runs.
        generated = root / relative
        if not generated.is_file() or not syntax_delimiters_ok(
                generated.read_text(encoding="utf-8")):
            failures.append(str(relative) + ": invalid generated Java source")
    print(f"CHECKED: {len(protected)} upstream Java files "
          f"({len(changed)} modified), {len(added)} generated helpers, "
          f"{checked_methods} original method declarations")

    keyboard = (root / path_for("Components/CustomPhoneKeyboardView.java")).read_text(encoding="utf-8")
    for symbol in (
        "setButtonBackground(", "lastBackButtonColor", "lastButtonsSelectorColor",
        "getButtonDrawable(", "void updateColors(",
    ):
        if symbol not in keyboard:
            failures.append("CustomPhoneKeyboardView missing native symbol: " + symbol)
    settings = (root / path_for("SettingsActivity.java")).read_text(encoding="utf-8")
    if "openDebugMenu();" in settings and "void openDebugMenu(" not in settings:
        failures.append("SettingsActivity calls removed openDebugMenu()")
    connections = (root / path_for("ConnectionsManager.java")).read_text(encoding="utf-8")
    if 'appVersion = nabdhVersionName + " (" + pInfo.versionCode + ")";' not in connections:
        failures.append("Generated initConnection app_version must derive from actual package version")
    # The app title is registered at Telegram's API developer console and
    # is NOT client-modifiable. Never spoof it in Telegram session objects.
    if "session.app_name =" in (
        (root / path_for("Cells/SessionCell.java")).read_text(encoding="utf-8")
        + (root / path_for("SessionBottomSheet.java")).read_text(encoding="utf-8")
    ):
        failures.append("Native Telegram session app_name must not be mutated")

    if failures:
        for failure in failures:
            print("FAIL: " + failure, file=sys.stderr)
        raise SystemExit("Upstream API preservation preflight failed")
    print("PASS: pinned Telegram method and critical field preservation preflight")

def self_test():
    fixture = """public class Example {
        // public void notARealMethod() {}
        String literal = "private void fake() {}";
        private static void setButtonBackground(View v, int idx) { }
        protected int updateColors() { return 1; }
        public void updateColors(int number) { }
    }"""
    assert "notARealMethod" not in declared_methods(fixture)
    assert "fake" not in declared_methods(fixture)
    assert declared_methods(fixture)["setButtonBackground"] == 1
    assert declared_methods(fixture)["updateColors"] == 2
    assert declared_methods(fixture)["updateColors"] > declared_methods(
        fixture.replace("public void updateColors(int number) { }", "")
    )["updateColors"]
    assert mask_noncode("/* hi */ public void ok() {}").count("ok") == 1
    assert syntax_delimiters_ok(fixture)
    assert not syntax_delimiters_ok(fixture + " public void deleted(int x) {")
    assert syntax_delimiters_ok('class C { String s = "{ [ )"; }')
    overload = """public class Example {
        public void run(java.util.Map<String, Integer> arg) {}
        public void run(int left, int right) {}
        public void run(@Some(value = {1, 2}) int value, boolean flag) {}
    }"""
    assert declared_method_arities(overload)[("run", 1)] == 1
    assert declared_method_arities(overload)[("run", 2)] == 2
    # An erased two-parameter overload is invisible to name-only counts if
    # replaced by a one-parameter overload; the new guard must reject it.
    switched = overload.replace("run(int left, int right)",
                                "run(String replacement)")
    assert declared_methods(overload) == declared_methods(switched)
    assert declared_method_arities(overload) - declared_method_arities(switched)
    assert declared_types(overload)[("class", "Example")] == 1
    assert declared_types(overload.replace("class Example", "class Renamed")) != declared_types(overload)
    print("PASS: upstream API preservation parser and overload self-tests")

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        self_test()
    elif len(sys.argv) == 2 and Path(sys.argv[1]).is_dir():
        assert_compatible(Path(sys.argv[1]).resolve())
    else:
        raise SystemExit("Usage: check-upstream-api-preservation.py --self-test | TELEGRAM_SOURCE")
