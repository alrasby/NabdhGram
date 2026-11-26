package net.nabdhserv.cardtest;

import android.app.Instrumentation;
import android.os.Bundle;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.RectF;
import java.io.FileOutputStream;
import org.telegram.ui.Components.NabdhCardRenderer;
import org.telegram.ui.Components.NabdhCardGeometry;

/** Exercises production renderer on Android Canvas, without a Telegram login. */
public final class CardProbe extends Instrumentation {
    private final NabdhCardRenderer renderer = new NabdhCardRenderer();
    private static void require(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    @Override public void onCreate(Bundle args) {
        super.onCreate(args);
        start();
    }
    private Bitmap frame(int offset, boolean dark) {
        Bitmap b = Bitmap.createBitmap(360,80,Bitmap.Config.ARGB_8888);
        Canvas c = new Canvas(b);
        RectF rect = new RectF(7,3,353,77);
        int fill = dark ? 0xff243039 : 0xffc3e1df;
        int reveal = dark ? 0xff355c60 : 0xff77b9b9;
        int save = c.save();
        renderer.clip(c,rect,17);
        renderer.reveal(c,rect,17,reveal);
        c.translate(offset,0);
        renderer.content(c,rect,17,1,fill,fill,0);
        c.restoreToCount(save);
        require(b.getPixel(0,40) == Color.TRANSPARENT, "left gutter");
        require(b.getPixel(359,40) == Color.TRANSPARENT, "right gutter");
        require(b.getPixel(7,3) == Color.TRANSPARENT, "corner leak");
        require(b.getPixel(180,0) == Color.TRANSPARENT, "top gutter");
        int contentX = offset > 0 ? 320 : 40;
        require(b.getPixel(contentX,40) == fill, "moving content color");
        if (offset >= 60) require(b.getPixel(25,40) == reveal, "right reveal color");
        if (offset <= -60) require(b.getPixel(335,40) == reveal, "left reveal color");
        return b;
    }
    private void save(String name, Bitmap b) throws Exception {
        try (FileOutputStream out = getTargetContext().openFileOutput(name+".png",0)) {
            require(b.compress(Bitmap.CompressFormat.PNG,100,out),"PNG capture");
        } finally { b.recycle(); }
    }
    @Override public void onStart() {
        Bundle result = new Bundle();
        try {
            save("rest",frame(0,false));
            save("right",frame(110,false));
            save("left",frame(-110,false));
            save("dark",frame(110,true));
            for (int cycle=0; cycle<25; cycle++) {
                for (int offset=-212; offset<=212; offset+=4) {
                    Bitmap b=frame(offset,cycle%2==0);
                    b.recycle();
                }
            }
            for (int i=0;i<4;i++) {
                require(NabdhCardGeometry.acceptTap(true,0,0,8,i,i),"tap "+i);
                require(!NabdhCardGeometry.acceptTap(false,0,0,8,i,i),"cancel "+i);
                require(!NabdhCardGeometry.acceptTap(true,9,0,8,i,i),"drag "+i);
            }
            require(NabdhCardGeometry.canMoveToFolder(43,42,1),"archive policy");
            require(!NabdhCardGeometry.canMoveToFolder(42,42,1),"self archive policy");
            require(NabdhCardGeometry.canMoveToFolder(43,42,0),"unarchive policy");
            result.putString("stream","\nCARD_GATE_PASS: Android Canvas pixels, 2675 frames, tap and archive policy\n");
            finish(-1,result);
        } catch(Throwable error) {
            result.putString("stream","\nCARD_GATE_FAIL: "+error.toString()+"\n");
            finish(0,result);
        }
    }
}
