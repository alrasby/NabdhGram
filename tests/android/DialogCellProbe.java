package net.nabdhserv.cardtest;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.os.Bundle;
import android.os.SystemClock;
import android.util.Log;
import android.view.MotionEvent;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.RandomAccessFile;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.Arrays;
import android.view.ViewGroup;

/** Runs in the debug application's process and renders its actual DialogCell. */
public final class DialogCellProbe extends Instrumentation {
    private static final String PERSISTED_THEME = "NabdhGram • Soft Mint";
    private static final String PERSISTED_NIGHT_THEME = "NabdhGram • Dark Glass";
    private static final int PERSISTED_STYLE = 2;
    private String phase;

    @Override public void onCreate(Bundle arguments) {
        super.onCreate(arguments);
        phase = arguments == null ? null : arguments.getString("phase");
        start();
    }

    @Override public void onStart() {
        Bundle result = new Bundle();
        Throwable[] failure = new Throwable[1];
        runOnMainSync(() -> {
            try {
                if ("save-theme".equals(phase) || "verify-theme".equals(phase)) {
                    exerciseThemeRestart();
                } else {
                    exerciseCell();
                }
            } catch (Throwable error) {
                failure[0] = error;
            }
        });
        if (failure[0] == null) {
            String success = phase == null
                    ? "DIALOG_CELL_PASS: 500 gesture cycles, 500 render cycles, tray dispatch and native local action transitions"
                    : "THEME_RESTART_PASS: " + phase;
            result.putString("stream", "\n" + success + "\n");
            finish(Activity.RESULT_OK, result);
        } else {
            result.putString("stream", "\nDIALOG_CELL_FAIL: " + Log.getStackTraceString(failure[0]));
            finish(Activity.RESULT_CANCELED, result);
        }
    }

    private void exerciseThemeRestart() throws Exception {
        Context app = getTargetContext();
        ClassLoader loader = app.getClassLoader();
        loader.loadClass("org.telegram.messenger.ApplicationLoader")
                .getMethod("postInitApplication").invoke(null);
        Class<?> theme = loader.loadClass("org.telegram.ui.ActionBar.Theme");
        Class<?> info = loader.loadClass("org.telegram.ui.ActionBar.Theme$ThemeInfo");
        Class<?> appearance = loader.loadClass("org.telegram.ui.Components.NabdhAppearancePrefs");
        android.content.SharedPreferences prefs = (android.content.SharedPreferences)
                loader.loadClass("org.telegram.messenger.MessagesController")
                        .getMethod("getGlobalMainSettings").invoke(null);
        Object selected = theme.getMethod("getTheme", String.class).invoke(null, PERSISTED_THEME);
        Object night = theme.getMethod("getTheme", String.class).invoke(null, PERSISTED_NIGHT_THEME);
        if (selected == null || night == null) throw new AssertionError("Bundled day or night theme missing");
        if ("save-theme".equals(phase)) {
            theme.getMethod("applyTheme", info, boolean.class, boolean.class)
                    .invoke(null, selected, true, false);
            appearance.getMethod("setUiStyle", Context.class, int.class)
                    .invoke(null, app, PERSISTED_STYLE);
            theme.getMethod("setCurrentNightTheme", info).invoke(null, night);
            theme.getMethod("saveAutoNightThemeConfig").invoke(null);
        }
        Object current = theme.getMethod("getCurrentTheme").invoke(null);
        int style = (Integer) appearance.getMethod("uiStyle").invoke(null);
        String savedTheme = prefs.getString("theme", null);
        String savedNightTheme = prefs.getString("nighttheme", null);
        if (current != selected || style != PERSISTED_STYLE || !PERSISTED_THEME.equals(savedTheme)
                || !PERSISTED_NIGHT_THEME.equals(savedNightTheme)
                || theme.getMethod("getCurrentNightTheme").invoke(null) != night) {
            throw new AssertionError("Appearance mismatch in " + phase
                    + ": active theme=" + info.getMethod("getKey").invoke(current)
                    + ", saved theme=" + savedTheme + ", saved night theme=" + savedNightTheme
                    + ", UI style=" + style);
        }
        if ("save-theme".equals(phase)) {
            // Instrumentation exits without the normal Activity stop lifecycle.
            // Wait for preceding asynchronous writes without supplying replacement values.
            android.content.SharedPreferences stylePrefs =
                    app.getSharedPreferences("nabdh_appearance_packs_v1", Context.MODE_PRIVATE);
            if (!prefs.edit().commit() || !stylePrefs.edit().commit()) {
                throw new AssertionError("Could not flush pending appearance preferences to disk");
            }
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
        Class<?> appearance = loader.loadClass("org.telegram.ui.Components.NabdhAppearancePrefs");
        Method chooseStyle = appearance.getMethod("setUiStyle", Context.class, int.class);
        if (!Integer.valueOf(0).equals(appearance.getMethod("uiStyle").invoke(null))
                || Boolean.TRUE.equals(ownsCard.invoke(cell))
                || !Boolean.TRUE.equals(type.getMethod("nabdhCanSwipe").invoke(cell))) {
            throw new AssertionError("Classic should preserve native rows and swipe eligibility");
        }
        cell.setTranslationX(-Math.round(80 * density));
        if (Boolean.TRUE.equals(ownsCard.invoke(cell))) {
            throw new AssertionError("Classic left swipe should retain native drawing");
        }
        cell.setTranslationX(Math.round(80 * density));
        if (!Boolean.TRUE.equals(ownsCard.invoke(cell))) {
            throw new AssertionError("Classic right swipe should use the rectangular tray");
        }
        cell.setTranslationX(0);
        exerciseBundledThemes(app, loader, appearance, chooseStyle);
        exerciseThemeImport(app, loader);
        chooseStyle.invoke(null, app, 3);
        if (!Boolean.TRUE.equals(ownsCard.invoke(cell))) {
            throw new AssertionError("Fixture does not use production card rendering");
        }
        exerciseSettingsRows(app, loader, density);
        exerciseNativeActions(loader, app);
        exerciseTray(cell, type, loader, width, density);
        exerciseController(cell, type, loader, width, density, app);
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

    private void exerciseBundledThemes(Context app, ClassLoader loader, Class<?> appearance,
            Method chooseStyle) throws Exception {
        Class<?> theme = loader.loadClass("org.telegram.ui.ActionBar.Theme");
        Class<?> themeInfo = loader.loadClass("org.telegram.ui.ActionBar.Theme$ThemeInfo");
        Method current = theme.getMethod("getCurrentTheme");
        Method apply = theme.getMethod("applyTheme", themeInfo, boolean.class, boolean.class);
        Method lookup = theme.getMethod("getTheme", String.class);
        Method active = theme.getMethod("getActiveTheme");
        Method hasWallpaper = theme.getMethod("hasWallpaperFromTheme");
        Method selectedStyle = appearance.getMethod("uiStyle");
        Object original = current.invoke(null);
        String[] names = {"Siri Glass Refined", "Soft Mint", "Dark Glass", "Gray Avalanche Sand"};
        try {
            for (String name : names) {
                Object bundled = lookup.invoke(null, "NabdhGram • " + name);
                if (bundled == null) throw new AssertionError("Missing bundled theme: " + name);
                apply.invoke(null, bundled, false, false);
                for (int style = 0; style < 4; style++) {
                    chooseStyle.invoke(null, app, style);
                    if (current.invoke(null) != bundled || active.invoke(null) != bundled
                            || !Boolean.TRUE.equals(hasWallpaper.invoke(null))
                            || !Integer.valueOf(style).equals(selectedStyle.invoke(null))) {
                        throw new AssertionError("Theme/style independence failed: " + name + "/" + style);
                    }
                }
            }
        } finally {
            apply.invoke(null, original, false, false);
        }
        if (current.invoke(null) != original) throw new AssertionError("Native theme restoration failed");
        status("Theme integration: four bundled themes applied and restored, 16 independent style combinations");
    }

    private void exerciseThemeImport(Context app, ClassLoader loader) throws Exception {
        Class<?> theme = loader.loadClass("org.telegram.ui.ActionBar.Theme");
        Class<?> remote = loader.loadClass("org.telegram.tgnet.TLRPC$TL_theme");
        Class<?> themeInfo = loader.loadClass("org.telegram.ui.ActionBar.Theme$ThemeInfo");
        Method preview = theme.getMethod("applyThemeFile", File.class, String.class,
                remote, boolean.class);
        Method current = theme.getMethod("getCurrentTheme");
        Method restore = theme.getMethod("applyPreviousTheme");
        Object before = current.invoke(null);
        File input = File.createTempFile("nabdh-theme-probe", ".attheme", app.getCacheDir());
        Object personalCopy = null;
        try {
            try (InputStream asset = app.getAssets().open("nabdh_soft_mint.attheme");
                    FileOutputStream destination = new FileOutputStream(input)) {
                byte[] buffer = new byte[8192];
                int count;
                while ((count = asset.read(buffer)) != -1) destination.write(buffer, 0, count);
            }
            if (preview.invoke(null, input, "Local visual check", null, true) == null) {
                throw new AssertionError("Verified theme copy could not enter native preview");
            }
            restore.invoke(null);
            if (current.invoke(null) != before) {
                throw new AssertionError("Closing local preview did not restore the previous theme");
            }
            String copyName = input.getName();
            personalCopy = preview.invoke(null, input, copyName, null, false);
            if (personalCopy == null || current.invoke(null) != personalCopy
                    || theme.getMethod("getTheme", String.class).invoke(null, copyName) != personalCopy
                    || theme.getMethod("getTheme", String.class).invoke(null, PERSISTED_THEME) == personalCopy
                    || !Boolean.TRUE.equals(theme.getMethod("hasWallpaperFromTheme").invoke(null))) {
                throw new AssertionError("Native import did not create an independent theme with its wallpaper");
            }
            theme.getMethod("applyTheme", themeInfo, boolean.class, boolean.class)
                    .invoke(null, before, true, false);
            try (RandomAccessFile file = new RandomAccessFile(input, "rw")) {
                file.setLength(21L * 1024 * 1024);
            }
            if (preview.invoke(null, input, "Oversize fixture", null, true) != null
                    || current.invoke(null) != before) {
                throw new AssertionError("Oversize theme reached native preview");
            }
        } finally {
            if (personalCopy != null) theme.getMethod("deleteTheme", themeInfo).invoke(null, personalCopy);
            input.delete();
        }
        status("Theme import: local preview, restoration, independent wallpaper copy and oversize rejection");
    }

    private void exerciseSettingsRows(Context app, ClassLoader loader, float density) throws Exception {
        Class<?> renderer = loader.loadClass("org.telegram.ui.Components.NabdhCompactSettings");
        Method row = renderer.getMethod("row", Context.class, LinearLayout.class, String.class,
                String.class, int.class, Runnable.class);
        Field rtl = loader.loadClass("org.telegram.messenger.LocaleController").getField("isRTL");
        boolean original = rtl.getBoolean(null);
        int icon = loader.loadClass("org.telegram.messenger.R$drawable").getField("settings_chat").getInt(null);
        int[] clicks = {0};
        try {
            for (boolean arabic : new boolean[]{false, true}) {
                rtl.setBoolean(null, arabic);
                LinearLayout screen = new LinearLayout(app);
                screen.setOrientation(LinearLayout.VERTICAL);
                String title = arabic ? "إدارة التخزين الذكية" : "Smart Storage";
                String summary = arabic ? "تعرض هذه الشاشة تفاصيل مساحة التخزين المحلية والوسائط وقواعد البيانات وملفات التطبيق الأخرى"
                        : "Inspect the local storage footprint for media, databases and other app files without deleting anything.";
                row.invoke(null, app, screen, title, summary, icon, (Runnable) () -> clicks[0]++);
                int width = Math.round(270 * density);
                screen.measure(View.MeasureSpec.makeMeasureSpec(width, View.MeasureSpec.EXACTLY),
                        View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED));
                screen.layout(0, 0, width, screen.getMeasuredHeight());
                LinearLayout group = (LinearLayout) screen.getChildAt(0);
                LinearLayout option = (LinearLayout) group.getChildAt(0);
                View leading = option.getChildAt(0);
                View trailing = option.getChildAt(2);
                LinearLayout labels = (LinearLayout) option.getChildAt(1);
                TextView description = (TextView) labels.getChildAt(1);
                if (!((arabic ? trailing : leading) instanceof ImageView)
                        || leading.getRight() > labels.getLeft()
                        || labels.getRight() > trailing.getLeft()
                        || description.getLineCount() <= 2
                        || description.getLayout().getEllipsisCount(description.getLineCount() - 1) != 0
                        || !option.performClick()) {
                    throw new AssertionError("Settings row layout/action failed for RTL=" + arabic);
                }
            }
        } finally {
            rtl.setBoolean(null, original);
        }
        if (clicks[0] != 2) throw new AssertionError("Unexpected settings callback count");
        status("Nabdh settings: physical RTL/LTR placement, full summary and row callback verified");
    }

    private void status(String message) {
        Bundle status = new Bundle();
        status.putString("stream", "\n" + message + "\n");
        sendStatus(0, status);
    }

    private void exerciseNativeActions(ClassLoader loader, Context app) throws Exception {
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
            Class<?> peer = loader.loadClass("org.telegram.tgnet.TLRPC$InputPeer");
            Method pin = controllerType.getMethod("pinDialog",
                    long.class, boolean.class, peer, long.class);
            Field pinned = dialog.getClass().getField("pinned");
            for (boolean expected : new boolean[]{true, false}) {
                if (!Boolean.TRUE.equals(pin.invoke(controller, id, expected, null, 0L))
                        || pinned.getBoolean(dialog) != expected) {
                    throw new AssertionError("Native pin transition failed");
                }
            }

            Class<?> notifications = loader.loadClass("org.telegram.messenger.NotificationsController");
            Object notifier = notifications.getMethod("getInstance", int.class).invoke(null, account);
            Method setMute = notifications.getMethod("setDialogNotificationsSettings",
                    long.class, long.class, int.class);
            Method isMuted = controllerType.getMethod("isDialogMuted", long.class, long.class);
            setMute.invoke(notifier, id, 0L, notifications.getField("SETTING_MUTE_FOREVER").getInt(null));
            if (!Boolean.TRUE.equals(isMuted.invoke(controller, id, 0L))) {
                throw new AssertionError("Native mute did not take effect");
            }
            setMute.invoke(notifier, id, 0L, notifications.getField("SETTING_MUTE_UNMUTE").getInt(null));
            if (!Boolean.FALSE.equals(isMuted.invoke(controller, id, 0L))) {
                throw new AssertionError("Native unmute did not take effect");
            }

            Class<?> reminder = loader.loadClass("org.telegram.ui.NabdhSwipeReminder");
            Method scheduled = reminder.getMethod("getScheduledTime", Context.class, int.class, long.class);
            Method cancelReminder = reminder.getMethod("cancel", Context.class, int.class, long.class);
            long when = System.currentTimeMillis() + 3_600_000L;
            try {
                reminder.getMethod("schedule", Context.class, int.class, long.class, long.class)
                        .invoke(null, app, account, id, when);
                if (!Long.valueOf(when).equals(scheduled.invoke(null, app, account, id))) {
                    throw new AssertionError("Reminder time was not stored");
                }
            } finally {
                cancelReminder.invoke(null, app, account, id);
            }
            if (!Long.valueOf(0).equals(scheduled.invoke(null, app, account, id))) {
                throw new AssertionError("Reminder time survived cancellation");
            }
            controllerType.getMethod("markDialogAsUnread", long.class, peer, long.class)
                    .invoke(controller, id, null, 0L);
            if (!dialog.getClass().getField("unread_mark").getBoolean(dialog)) {
                throw new AssertionError("Native unread mark was not applied");
            }
        } finally {
            remove.invoke(dialogs, id);
        }
        status("Native local states: archive, unarchive, service-chat rejection, pin, unpin, mute, unmute, reminder schedule/cancel and unread");
    }

    private void exerciseController(View cell, Class<?> type, ClassLoader loader, int width,
            float density, Context context) throws Exception {
        Class<?> recyclerType = loader.loadClass("androidx.recyclerview.widget.RecyclerView");
        ViewGroup recycler = (ViewGroup) recyclerType.getConstructor(Context.class).newInstance(context);
        Class<?> managerType = loader.loadClass("androidx.recyclerview.widget.RecyclerView$LayoutManager");
        Object manager = loader.loadClass("androidx.recyclerview.widget.LinearLayoutManager")
                .getConstructor(Context.class).newInstance(context);
        recyclerType.getMethod("setLayoutManager", managerType).invoke(recycler, manager);
        FrameLayout parent = new FrameLayout(context);
        parent.addView(recycler);
        int height = cell.getMeasuredHeight();
        recycler.layout(0, 0, width, height);
        recycler.addView(cell);
        cell.layout(0, 0, width, height);

        String controllerName = "org.telegram.ui.Components.NabdhSmartSwipeController";
        Class<?> controllerType = loader.loadClass(controllerName);
        Class<?> hostType = loader.loadClass(controllerName + "$Host");
        Class<?> callbackType = loader.loadClass(type.getName() + "$NabdhSmartAction");
        Method configure = type.getMethod("nabdhSetSmartSwipeActions", callbackType,
                boolean.class, boolean.class, boolean.class);
        int[] executions = new int[4];
        Object host = Proxy.newProxyInstance(loader, new Class<?>[]{hostType},
                (proxy, method, arguments) -> {
                    switch (method.getName()) {
                        case "canBegin":
                        case "isEligible":
                            return true;
                        case "configure":
                            configure.invoke(arguments[0], arguments[1], false, false, false);
                            return true;
                        case "runAction":
                            executions[(Integer) arguments[1]]++;
                            return null;
                        default:
                            return null;
                    }
                });
        Object controller = controllerType.getConstructor(hostType).newInstance(host);
        Method intercept = controllerType.getMethod("onInterceptTouchEvent", recyclerType, MotionEvent.class);
        Method touch = controllerType.getMethod("onTouchEvent", recyclerType, MotionEvent.class);
        Method cancel = controllerType.getMethod("cancel");
        float x = Math.round(42 * density);
        float y = height / 2f;
        long down = SystemClock.uptimeMillis();
        try {
            if (event(intercept, controller, recycler, down, MotionEvent.ACTION_DOWN, x, y)
                    || event(intercept, controller, recycler, down, MotionEvent.ACTION_MOVE,
                        x, y + 32 * density)) {
                throw new AssertionError("Vertical gesture claimed by Smart Swipe");
            }
            for (int cycle = 0; cycle < 500; cycle++) {
                down = SystemClock.uptimeMillis();
                if (event(intercept, controller, recycler, down, MotionEvent.ACTION_DOWN, x, y)
                        || !event(intercept, controller, recycler, down, MotionEvent.ACTION_MOVE,
                            x + 120 * density, y)) {
                    throw new AssertionError("Horizontal gesture was misclassified");
                }
                event(touch, controller, recycler, down, MotionEvent.ACTION_MOVE, x + 212 * density, y);
                if (cell.getTranslationX() < 200 * density) {
                    throw new AssertionError("DialogCell did not move with the gesture");
                }
                event(touch, controller, recycler, down, MotionEvent.ACTION_CANCEL, x + 212 * density, y);
                cancel.invoke(controller);
                if (cell.getTranslationX() != 0 || Arrays.stream(executions).sum() != 0) {
                    throw new AssertionError("Cancellation left an offset or executed an action");
                }
            }
            Field trayField = type.getDeclaredField("nabdhSmartBar");
            trayField.setAccessible(true);
            ViewGroup tray = (ViewGroup) trayField.get(cell);
            for (int action = 0; action < 4; action++) {
                down = SystemClock.uptimeMillis();
                event(intercept, controller, recycler, down, MotionEvent.ACTION_DOWN, x, y);
                if (!event(intercept, controller, recycler, down, MotionEvent.ACTION_MOVE,
                        x + 212 * density, y)) {
                    throw new AssertionError("Could not reveal action tray");
                }
                event(touch, controller, recycler, down, MotionEvent.ACTION_UP, x + 212 * density, y);
                View button = tray.getChildAt(action);
                float buttonX = tray.getLeft() + (button.getLeft() + button.getRight()) / 2f;
                float buttonY = tray.getTop() + (button.getTop() + button.getBottom()) / 2f;
                down = SystemClock.uptimeMillis();
                if (!event(intercept, controller, recycler, down, MotionEvent.ACTION_DOWN, buttonX, buttonY)) {
                    throw new AssertionError("Tray did not claim action tap");
                }
                event(touch, controller, recycler, down, MotionEvent.ACTION_UP, buttonX, buttonY);
                event(touch, controller, recycler, down, MotionEvent.ACTION_UP, buttonX, buttonY);
                if (executions[action] != 1 || Arrays.stream(executions).sum() != action + 1) {
                    throw new AssertionError("Missing, duplicate or incorrect action: " + action);
                }
                cancel.invoke(controller);
            }
        } finally {
            cancel.invoke(controller);
            recycler.removeView(cell);
        }
    }

    private boolean event(Method method, Object controller, View recycler, long down,
            int action, float x, float y) throws Exception {
        MotionEvent event = MotionEvent.obtain(down, SystemClock.uptimeMillis(), action, x, y, 0);
        try {
            return Boolean.TRUE.equals(method.invoke(controller, recycler, event));
        } finally {
            event.recycle();
        }
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
