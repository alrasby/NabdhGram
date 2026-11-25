package org.telegram.ui.Components;

import android.app.AlertDialog;
import android.content.Context;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import java.io.File;
import java.util.ArrayDeque;
import java.util.Locale;
import java.util.HashSet;
import java.util.TreeMap;
import java.util.concurrent.atomic.AtomicBoolean;
import org.telegram.messenger.LocaleController;

/** Read-only private storage inventory; no permissions, network, or deletion. */
public final class NabdhStorageAudit {
    private static final AtomicBoolean running = new AtomicBoolean();
    private NabdhStorageAudit() {}
    private static String size(long bytes) {
        return String.format(Locale.US, "%.2f MiB", bytes / 1048576.0);
    }
    private static String group(String name, String parent) {
        String lower = name.toLowerCase(Locale.ROOT);
        if (lower.endsWith(".db") || lower.endsWith(".db-wal") || lower.endsWith(".db-shm")
                || lower.endsWith(".sqlite") || lower.endsWith(".sqlite-wal")
                || lower.endsWith(".sqlite-shm") || lower.endsWith(".sqlite-journal")) return "db";
        if (lower.endsWith(".tflite") || lower.endsWith(".task") || lower.endsWith(".gguf")
                || lower.endsWith(".onnx") || lower.endsWith(".bin") && parent.contains("model")) return "model";
        if (parent.contains("nabdh_camera")) return "camera";
        if (lower.endsWith(".jpg") || lower.endsWith(".jpeg") || lower.endsWith(".png")
                || lower.endsWith(".webp") || lower.endsWith(".mp4") || lower.endsWith(".ogg")
                || lower.endsWith(".opus") || lower.endsWith(".mp3") || lower.endsWith(".pdf")) return "media";
        if (lower.endsWith(".attheme")) return "theme";
        return "other";
    }
    private static long walk(File root, TreeMap<String,Long> totals, HashSet<String> visited,
                             AtomicBoolean cancelled, boolean[] partial) {
        if (root == null || !root.isDirectory()) return 0;
        long bytes = 0;
        try {
            String base = root.getCanonicalPath();
            ArrayDeque<File> queue = new ArrayDeque<>();
            queue.add(root);
            int count = 0;
            while (!queue.isEmpty() && !cancelled.get()) {
                if (++count > 100000) { partial[0] = true; break; }
                File next = queue.removeFirst();
                String absolute = next.getAbsolutePath();
                String canonical = next.getCanonicalPath();
                if (!canonical.equals(base) && !canonical.startsWith(base + File.separator)) continue;
                if (!absolute.equals(canonical) && !next.equals(root)) continue;
                if (!visited.add(canonical)) continue;
                if (next.isDirectory()) {
                    File[] children = next.listFiles();
                    if (children == null) { partial[0] = true; continue; }
                    for (File child : children) queue.addLast(child);
                } else if (next.isFile()) {
                    long n = next.length();
                    bytes += n;
                    String key = group(next.getName(), canonical.toLowerCase(Locale.ROOT));
                    totals.put(key, totals.getOrDefault(key, 0L) + n);
                }
            }
        } catch (Exception e) { partial[0] = true; }
        return bytes;
    }
    public static void show(Context context) {
        final boolean ar = LocaleController.isRTL;
        if (!running.compareAndSet(false, true)) return;
        final AtomicBoolean cancelled = new AtomicBoolean();
        final AlertDialog progress;
        try {
            progress = new AlertDialog.Builder(context)
                    .setTitle(ar ? "إدارة التخزين الذكية" : "Smart Storage")
                    .setMessage(ar ? "جارٍ تحليل الملفات المحلية…" : "Analyzing local files…")
                    .setNegativeButton(ar ? "إلغاء" : "Cancel", (d,w) -> cancelled.set(true)).create();
            progress.setOnDismissListener(d -> cancelled.set(true));
            progress.show();
        } catch (RuntimeException e) { running.set(false); return; }
        final Context app = context.getApplicationContext();
        new Thread(() -> {
            try {
                TreeMap<String,Long> totals = new TreeMap<>();
                HashSet<String> visited = new HashSet<>();
                boolean[] partial = {false};
                long cache = walk(app.getCacheDir(), totals, visited, cancelled, partial);
                for (File f : app.getExternalCacheDirs()) cache += walk(f, totals, visited, cancelled, partial);
                long privateData = walk(new File(app.getApplicationInfo().dataDir), totals, visited, cancelled, partial);
                long external = 0;
                for (File f : app.getExternalFilesDirs(null)) external += walk(f, totals, visited, cancelled, partial);
                StringBuilder out = new StringBuilder();
                out.append(ar ? "بيانات داخلية (عدا الكاش): " : "Internal data excluding cache: ").append(size(privateData));
                out.append(ar ? "\nملفات خارجية خاصة: " : "\nApp-specific external files: ").append(size(external));
                out.append(ar ? "\nالكاش: " : "\nCache: ").append(size(cache));
                String[] keys = {"db","media","camera","model","theme","other"};
                String[] names = ar ? new String[]{"قواعد البيانات وملفاتها","وسائط معروفة","صور الكاميرا الخاصة","ملفات النماذج","الثيمات","ملفات أخرى"}
                        : new String[]{"Databases and sidecars","Recognized media","Private camera","Model files","Themes","Other files"};
                out.append(ar ? "\n\nتصنيف الملفات (يشمل الكاش):" : "\n\nFile categories (including cache):");
                for (int i=0;i<keys.length;i++) out.append("\n").append(names[i]).append(": ").append(size(totals.getOrDefault(keys[i],0L)));
                out.append(ar ? "\n\nهذا تقدير للملفات المقروءة، وليس قياس Android الكامل. لم تُحذف أي ملفات." : "\n\nReadable-file estimate, not Android's full storage accounting. No files deleted.");
                if (partial[0]) out.append(ar ? "\nالنتيجة جزئية." : "\nPartial scan.");
                String result = out.toString();
                new Handler(Looper.getMainLooper()).post(() -> {
                    if (cancelled.get() || !progress.isShowing()) return;
                    progress.dismiss();
                    try { new AlertDialog.Builder(context).setTitle(ar ? "تحليل التخزين" : "Storage analysis")
                            .setMessage(result).setPositiveButton(ar ? "إغلاق" : "Close", null)
                            .setNeutralButton(ar ? "نسخ التقرير" : "Copy report", (d,w) -> {
                                android.content.ClipboardManager clipboard = (android.content.ClipboardManager)
                                        context.getSystemService(Context.CLIPBOARD_SERVICE);
                                if (clipboard != null) clipboard.setPrimaryClip(android.content.ClipData.newPlainText("Storage", result));
                            }).show(); } catch (RuntimeException ignored) {}
                });
            } finally { running.set(false); }
        }, "NabdhStorageAudit").start();
    }
}
