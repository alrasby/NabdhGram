package net.nabdhserv.cardtest;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import java.io.FileOutputStream;
import java.lang.reflect.Method;

/** Runs in the debug application's process and renders its actual DialogCell. */
public final class DialogCellProbe extends Instrumentation {
    @Override public void onCreate(Bundle arguments) {
        super.onCreate(arguments);
        start();
    }

    @Override public void onStart() {
        Bundle result = new Bundle();
        Throwable[] failure = new Throwable[1];
        runOnMainSync(() -> {
            try {
                exerciseCell();
            } catch (Throwable error) {
                failure[0] = error;
            }
        });
        if (failure[0] == null) {
            result.putString("stream", "\nDIALOG_CELL_PASS: 500 render cycles with both offsets\n");
            finish(Activity.RESULT_OK, result);
        } else {
            result.putString("stream", "\nDIALOG_CELL_FAIL: " + Log.getStackTraceString(failure[0]));
            finish(Activity.RESULT_CANCELED, result);
        }
    }

    private void exerciseCell() throws Exception {
        Context app = getTargetContext();
        ClassLoader loader = app.getClassLoader();
        loader.loadClass("org.telegram.messenger.ApplicationLoader")
                .getMethod("postInitApplication").invoke(null);
        String cellName = "org.telegram.ui.Cells.DialogCell";
        Class<?> type = loader.loadClass(cellName);
        Class<?> activity = loader.loadClass("org.telegram.ui.DialogsActivity");
        Class<?> fixtureType = loader.loadClass(cellName + "$CustomDialog");
        Object fixture = fixtureType.getConstructor().newInstance();
        fixtureType.getField("id").setInt(fixture, 42);
        fixtureType.getField("name").set(fixture, "Card test chat");
        fixtureType.getField("message").set(fixture, "A local test message");
        fixtureType.getField("unread_count").setInt(fixture, 3);
        View cell = (View) type.getConstructor(activity, Context.class, boolean.class, boolean.class)
                .newInstance(null, app, false, false);
        type.getMethod("setDialog", fixtureType).invoke(cell, fixture);
        float density = app.getResources().getDisplayMetrics().density;
        int width = Math.round(360 * density);
        cell.measure(View.MeasureSpec.makeMeasureSpec(width, View.MeasureSpec.EXACTLY),
                View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED));
        cell.layout(0, 0, width, cell.getMeasuredHeight());
        Method ownsCard = type.getMethod("nabdhOwnsCard");
        if (!Boolean.TRUE.equals(ownsCard.invoke(cell))) {
            throw new AssertionError("Fixture does not use production card rendering");
        }
        Bitmap frame = Bitmap.createBitmap(width, cell.getHeight(), Bitmap.Config.ARGB_8888);
        try {
            int offset = Math.round(110 * density);
            for (int cycle = 0; cycle < 500; cycle++) {
                draw(cell, frame, 0, cycle == 0 ? "dialog-rest" : null, app);
                draw(cell, frame, offset, cycle == 0 ? "dialog-right" : null, app);
                draw(cell, frame, -offset, cycle == 0 ? "dialog-left" : null, app);
            }
        } finally {
            cell.setTranslationX(0);
            frame.recycle();
        }
    }

    private void draw(View cell, Bitmap frame, float offset, String evidence, Context app)
            throws Exception {
        cell.setTranslationX(offset);
        frame.eraseColor(0);
        cell.draw(new Canvas(frame));
        int middle = frame.getHeight() / 2;
        if (frame.getPixel(0, middle) != 0
                || frame.getPixel(frame.getWidth() - 1, middle) != 0
                || frame.getPixel(frame.getWidth() / 2, 0) != 0) {
            throw new AssertionError("Card painted into a gutter at offset " + offset);
        }
        if ((frame.getPixel(frame.getWidth() / 2, middle) >>> 24) == 0) {
            throw new AssertionError("Empty card viewport at offset " + offset);
        }
        if (evidence != null) {
            try (FileOutputStream output = app.openFileOutput(evidence + ".png", 0)) {
                if (!frame.compress(Bitmap.CompressFormat.PNG, 100, output)) {
                    throw new AssertionError("Unable to save " + evidence);
                }
            }
        }
    }
}
