#!/usr/bin/env python3
"""Execute the same Java geometry used by Android, without Android stubs."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = root / "overlay/java/NabdhCardGeometry.java"
press = source.with_name("NabdhSwipeActionPress.java")
motion = source.with_name("NabdhSwipeMotion.java")
harness = """import org.telegram.ui.Components.NabdhCardGeometry;
import org.telegram.ui.Components.NabdhSwipeActionPress;
import org.telegram.ui.Components.NabdhSwipeMotion;
import org.telegram.ui.Components.NabdhSwipeMotion.Decision;
public class CardGeometryTest {
    private static void require(boolean ok) {
        if (!ok) throw new AssertionError("Card geometry invariant failed");
    }
    public static void main(String[] args) {
        int cases = 0;
        for (int width = 24; width <= 1200; width += 7) {
            for (int x = -1500; x <= 1500; x += 3) {
                float l = 7, r = width - 7;
                float a = NabdhCardGeometry.revealRight(l,r,x);
                float b = NabdhCardGeometry.revealLeft(l,r,x);
                require(a >= l && a <= r && b >= l && b <= r);
                require(Math.abs((a-l) - Math.min(r-l, Math.max(0,x))) < .01);
                require(Math.abs((r-b) - Math.min(r-l, Math.max(0,-x))) < .01);
                require(NabdhCardGeometry.trayWidth(x,212) == Math.max(0,Math.min(212,x)));
                cases++;
            }
        }
        for (int down = -1; down <= 4; down++) {
            for (int up = -1; up <= 4; up++) {
                require(NabdhCardGeometry.acceptTap(true,0,0,8,down,up)
                        == (down >= 0 && down < 4 && down == up));
                require(!NabdhCardGeometry.acceptTap(false,0,0,8,down,up));
                require(!NabdhCardGeometry.acceptTap(true,8,0,8,down,up));
                require(!NabdhCardGeometry.acceptTap(true,0,-8,8,down,up));
            }
        }
        require(!NabdhCardGeometry.canMoveToFolder(42,42,1));
        require(!NabdhCardGeometry.canMoveToFolder(777000,42,1));
        require(NabdhCardGeometry.canMoveToFolder(43,42,1));
        require(NabdhCardGeometry.canMoveToFolder(-43,42,1));
        require(NabdhCardGeometry.canMoveToFolder(42,42,0));
        require(NabdhCardGeometry.hit(2,3,2,3,51,60));
        require(!NabdhCardGeometry.hit(51,3,2,3,51,60));
        require(!NabdhCardGeometry.hit(2,60,2,3,51,60));
        NabdhSwipeActionPress press = new NabdhSwipeActionPress();
        press.begin(3, 2, 20, 20);
        require(press.release(3, 21, 20, 8, 2) == 2);
        require(press.release(3, 21, 20, 8, 2) == -1);
        press.begin(3, 2, 20, 20);
        require(!press.update(3, 20, 29, 8, 2));
        require(press.release(3, 20, 20, 8, 2) == -1);
        press.begin(3, 2, 20, 20);
        require(press.release(4, 20, 20, 8, 2) == -1);
        press.begin(3, 2, 20, 20);
        press.cancel();
        require(press.release(3, 20, 20, 8, 2) == -1);
        require(NabdhSwipeMotion.classify(0, 8, 0, 8, 36) == Decision.PENDING);
        require(NabdhSwipeMotion.classify(0, 40, 8, 8, 36) == Decision.CLAIM);
        require(NabdhSwipeMotion.classify(0, -40, 8, 8, 36) == Decision.YIELD);
        require(NabdhSwipeMotion.classify(0, 40, 40, 8, 36) == Decision.YIELD);
        require(NabdhSwipeMotion.classify(120, -40, 8, 8, 36) == Decision.CLAIM);
        require(NabdhSwipeMotion.offset(120, -180, 212) == 0);
        require(NabdhSwipeMotion.offset(120, 180, 212) == 212);
        require(NabdhSwipeMotion.offset(120, -40, 212) == 80);
        System.out.println("PASS: 8 gesture direction and offset assertions");
        System.out.println("PASS: 6 action press assertions");
        System.out.println("PASS: " + cases + " reveal cases and tap cancellation/boundaries");
    }
}
"""
with tempfile.TemporaryDirectory() as directory:
    target = Path(directory)
    main = target / "CardGeometryTest.java"
    main.write_text(harness, encoding="utf-8")
    subprocess.run(["javac", "-d", str(target), str(source), str(press), str(motion), str(main)], check=True)
    subprocess.run(["java", "-cp", str(target), "CardGeometryTest"], check=True)
