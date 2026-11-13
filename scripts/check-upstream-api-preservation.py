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

def declared_methods(code):
    # Count rather than just set: an erased overload with another declaration
    # of the same name must still be reported.
    return Counter(m.group("name") for m in METHOD.finditer(mask_noncode(code)))

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
    for name in CRITICAL_FILES:
        relative = path_for(name)
        original = baseline(root, relative)
        generated = (root / relative).read_text(encoding="utf-8")
        before, after = declared_methods(original), declared_methods(generated)
        missing = before - after
        if missing:
            failures.append(
                str(relative) + ": erased native Java method declaration(s): "
                + ", ".join(f"{m} (x{n})" for m, n in sorted(missing.items()))
            )
        else:
            print(f"PASS: preserved {sum(before.values())} native method declarations: {relative}")

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
    print("PASS: upstream API preservation parser self-tests")

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        self_test()
    elif len(sys.argv) == 2 and Path(sys.argv[1]).is_dir():
        assert_compatible(Path(sys.argv[1]).resolve())
    else:
        raise SystemExit("Usage: check-upstream-api-preservation.py --self-test | TELEGRAM_SOURCE")
