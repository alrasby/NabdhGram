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
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.Arrays;
import android.view.ViewGroup;

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
            result.putString("stream", "\nDIALOG_CELL_PASS: baseline 500 render cycles, tray hit checks and native local folder move\n");
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
        exerciseNativeArchive(loader);
        exerciseTray(cell, type, loader, width, density);
        Bitmap frame = Bitmap.createBitmap(width, cell.getHeight(), Bitmap.Config.ARGB_8888);
        try {
            int offset = Math.round(110 * density);
            long[] frameTimes = new long[500];
            for (int cycle = 0; cycle < 500; cycle++) {
                long start = System.nanoTime();
                draw(cell, frame, 0, cycle == 0 ? "dialog-rest" : null, app);
                draw(cell, frame, offset, cycle == 0 ? "dialog-right" : null, app);
                draw(cell, frame, -offset, cycle == 0 ? "dialog-left" : null, app);
                frameTimes[cycle] = System.nanoTime() - start;
            }
            Arrays.sort(frameTimes);
            status("Three-frame software draw cycle, p50=" + frameTimes[250] / 1000
                    + "us p95=" + frameTimes[475] / 1000 + "us");
            draw(cell, frame, 0, "dialog-rest-after", app);
        } finally {
            cell.setTranslationX(0);
            frame.recycle();
        }
    }

    private void status(String message) {
        Bundle status = new Bundle();
        status.putString("stream", "\n" + message + "\n");
        sendStatus(0, status);
    }

    private void exerciseNativeArchive(ClassLoader loader) throws Exception {
        Class<?> controllerType = loader.loadClass("org.telegram.messenger.MessagesController");
        Class<?> configType = loader.loadClass("org.telegram.messenger.UserConfig");
        int account = configType.getField("selectedAccount").getInt(null);
        Object controller = controllerType.getMethod("getInstance", int.class).invoke(null, account);
        Object dialog = loader.loadClass("org.telegram.tgnet.TLRPC$TL_dialog")
                .getConstructor().newInstance();
        long id = (Long) loader.loadClass("org.telegram.messenger.DialogObject")
                .getMethod("makeEncryptedDialogId", long.class).invoke(null, 42L);
        dialog.getClass().getField("id").setLong(dialog, id);
        Object dialogs = controllerType.getField("dialogs_dict").get(controller);
        Method put = dialogs.getClass().getMethod("put", long.class, Object.class);
        Method remove = dialogs.getClass().getMethod("remove", long.class);
        Method move = controllerType.getMethod("addDialogToFolder",
                long.class, int.class, int.class, long.class);
        Field folder = dialog.getClass().getField("folder_id");
        put.invoke(dialogs, id, dialog);
        try {
            for (int destination : new int[]{1, 0}) {
                if (((Integer) move.invoke(controller, id, destination, -1, 0L)) <= 0
                        || folder.getInt(dialog) != destination) {
                    throw new AssertionError("Native local folder move failed: " + destination);
                }
            }
            if (!Integer.valueOf(0).equals(move.invoke(controller, 777000L, 1, -1, 0L))) {
                throw new AssertionError("Telegram service dialog accepted for archive");
            }
        } finally {
            remove.invoke(dialogs, id);
        }
        status("Native folder state: archived, restored, Telegram service dialog rejected");
    }

    private void exerciseTray(View cell, Class<?> type, ClassLoader loader, int width,
            float density) throws Exception {
        Class<?> callbackType = loader.loadClass(type.getName() + "$NabdhSmartAction");
        Method configure = type.getMethod("nabdhSetSmartSwipeActions", callbackType,
                boolean.class, boolean.class, boolean.class);
        Method hit = type.getMethod("nabdhSmartActionAt", float.class, float.class);
        Method perform = type.getMethod("nabdhPerformSmartAction", int.class);
        Method clear = type.getMethod("nabdhClearSmartSwipeActions");
        Field trayField = type.getDeclaredField("nabdhSmartBar");
        trayField.setAccessible(true);
        ViewGroup tray = (ViewGroup) trayField.get(cell);
        Field rtl = loader.loadClass("org.telegram.messenger.LocaleController").getField("isRTL");
        boolean originalDirection = rtl.getBoolean(null);
        int[] calls = new int[4];
        Object callback = Proxy.newProxyInstance(loader, new Class<?>[]{callbackType},
                (proxy, method, arguments) -> {
                    if ("onAction".equals(method.getName())) {
                        calls[(Integer) arguments[0]]++;
                    }
                    return null;
                });
        try {
            for (boolean direction : new boolean[]{false, true}) {
                rtl.setBoolean(null, direction);
                configure.invoke(cell, callback, true, true, true);
                cell.setTranslationX((float) Math.ceil(212 * density));
                // An unattached DialogCell does not propagate requestLayout().
                // Force a new layout to exercise the tray after changing direction.
                cell.forceLayout();
                cell.measure(View.MeasureSpec.makeMeasureSpec(width, View.MeasureSpec.EXACTLY),
                        View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED));
                cell.layout(0, 0, width, cell.getMeasuredHeight());
                int previousCenter = direction ? Integer.MAX_VALUE : Integer.MIN_VALUE;
                int expectedCalls = direction ? 2 : 1;
                for (int action = 0; action < 4; action++) {
                    View button = tray.getChildAt(action);
                    int center = (button.getLeft() + button.getRight()) / 2;
                    if (direction ? center >= previousCenter : center <= previousCenter) {
                        throw new AssertionError("Incorrect direction for action " + action);
                    }
                    previousCenter = center;
                    float x = tray.getLeft() + center;
                    float y = tray.getTop() + (button.getTop() + button.getBottom()) / 2f;
                    if (!Integer.valueOf(action).equals(hit.invoke(cell, x, y))) {
                        throw new AssertionError("Incorrect hit for action " + action);
                    }
                    perform.invoke(cell, action);
                    if (calls[action] != expectedCalls) {
                        throw new AssertionError("Incorrect dispatch for action " + action);
                    }
                    cell.setTranslationX(center / 2f);
                    if (!Integer.valueOf(-1).equals(hit.invoke(cell, x, y))) {
                        throw new AssertionError("Clipped action remains interactive");
                    }
                    cell.setTranslationX((float) Math.ceil(212 * density));
                }
                clear.invoke(cell);
                perform.invoke(cell, 0);
                if (calls[0] != expectedCalls) {
                    throw new AssertionError("Cleared action remains interactive");
                }
                cell.setTranslationX(0);
            }
        } finally {
            rtl.setBoolean(null, originalDirection);
            clear.invoke(cell);
            cell.setTranslationX(0);
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
