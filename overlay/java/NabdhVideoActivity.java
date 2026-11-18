package org.telegram.ui;

import android.Manifest;
import android.app.Activity;
import android.app.PictureInPictureParams;
import android.content.ClipData;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.res.Configuration;
import android.graphics.SurfaceTexture;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.params.StreamConfigurationMap;
import android.media.MediaRecorder;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.HandlerThread;
import android.provider.MediaStore;
import android.util.Range;
import android.util.Rational;
import android.util.Size;
import android.view.Surface;
import android.view.TextureView;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.Toast;
import androidx.core.content.FileProvider;
import org.telegram.ui.Components.NabdhHomePrefs;
import org.telegram.ui.Components.NabdhToolUi;
import org.telegram.messenger.LocaleController;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.util.Arrays;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/** Explicit Camera2/MediaRecorder video recorder, isolated from Telegram calls. */
public final class NabdhVideoActivity extends Activity {
    private static final int PERMISSION = 7401;
    private CameraManager manager;
    private HandlerThread worker;
    private Handler handler;
    private TextureView preview;
    private CameraDevice camera;
    private CameraCaptureSession session;
    private Surface previewSurface;
    private MediaRecorder recorder;
    private File temp;
    private volatile Uri lastVideo;
    // A bounded pending-recording queue prevents multi-GB storage backlogs.
    private final ThreadPoolExecutor disk = new ThreadPoolExecutor(
            1, 1, 30, TimeUnit.SECONDS, new ArrayBlockingQueue<>(2));
    private boolean opening, recording, configuring, active, enteringPip;
    private long generation;
    private long sessionGeneration;
    private String cameraId;
    private int lens = CameraCharacteristics.LENS_FACING_BACK;
    private int sensorOrientation = 90;
    private int frames = 30;
    private Size videoSize = new Size(1280, 720);
    private Range<Integer> fpsRange;
    private boolean eisAvailable;
    private Button recordButton, shareButton, pipButton;

    private String local(String english, String arabic) {
        return LocaleController.isRTL ? arabic : english;
    }
    private int dp(int n) {
        return Math.round(n * getResources().getDisplayMetrics().density);
    }
    private boolean option(String key) {
        return NabdhHomePrefs.enabled(this, key);
    }
    private void toast(String english, String arabic) {
        runOnUiThread(() -> Toast.makeText(this, local(english, arabic),
                Toast.LENGTH_LONG).show());
    }
    private Button control(String english, String arabic, Runnable click) {
        Button button = new Button(this);
        button.setAllCaps(false);
        button.setText(local(english, arabic));
        NabdhToolUi.styleButton(this, button);
        button.setOnClickListener(v -> click.run());
        return button;
    }
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        manager = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
        LinearLayout screen = new LinearLayout(this);
        screen.setOrientation(LinearLayout.VERTICAL);
        screen.setBackgroundColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundGray));
        screen.setLayoutDirection(LocaleController.isRTL ?
                View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        preview = new TextureView(this);
        screen.addView(preview, new LinearLayout.LayoutParams(-1, 0, 1));
        recordButton = control("Start recording", "بدء تسجيل الفيديو",
                () -> { if (recording) stopRecording(); else startRecording(); });
        screen.addView(recordButton, new LinearLayout.LayoutParams(-1, dp(52)));
        Button switchLens = control("Switch lens", "تبديل الكاميرا", () -> {
            if (recording || configuring) {
                toast("Stop recording before switching", "أوقف التسجيل قبل تبديل العدسة");
                return;
            }
            lens = lens == CameraCharacteristics.LENS_FACING_FRONT ?
                    CameraCharacteristics.LENS_FACING_BACK :
                    CameraCharacteristics.LENS_FACING_FRONT;
            if (option("camera_remember")) {
                getSharedPreferences("nabdh_ui_personalization_v1", MODE_PRIVATE)
                        .edit().putInt("camera_last_facing", lens).apply();
            }
            restart();
        });
        screen.addView(switchLens, new LinearLayout.LayoutParams(-1, dp(50)));
        pipButton = control("Floating PiP preview", "عرض فيديو عائم PiP", this::startPip);
        screen.addView(pipButton, new LinearLayout.LayoutParams(-1, dp(50)));
        shareButton = control("Share captured video in NabdhGram",
                "مشاركة الفيديو في نبض جرام", this::share);
        shareButton.setEnabled(false);
        screen.addView(shareButton, new LinearLayout.LayoutParams(-1, dp(50)));
        screen.addView(control("Video settings", "إعدادات الفيديو", () -> {
            Intent settings = new Intent(this, NabdhPersonalizeActivity.class);
            settings.putExtra(NabdhPersonalizeActivity.EXTRA_SECTION,
                    NabdhPersonalizeActivity.CAMERA);
            startActivity(settings);
        }), new LinearLayout.LayoutParams(-1, dp(50)));
        NabdhToolUi.install(this, screen, local("Nabdh Video Camera", "فيديو كاميرا نبض"));
        preview.setSurfaceTextureListener(new TextureView.SurfaceTextureListener() {
            @Override public void onSurfaceTextureAvailable(SurfaceTexture texture, int w, int h) {
                open();
            }
            @Override public void onSurfaceTextureSizeChanged(SurfaceTexture t, int w, int h) { }
            @Override public boolean onSurfaceTextureDestroyed(SurfaceTexture t) {
                stopRecording();
                closeCamera();
                return true;
            }
            @Override public void onSurfaceTextureUpdated(SurfaceTexture t) { }
        });
        if (option("camera_remember")) {
            lens = getSharedPreferences("nabdh_ui_personalization_v1", MODE_PRIVATE)
                    .getInt("camera_last_facing", CameraCharacteristics.LENS_FACING_BACK);
            if (lens != CameraCharacteristics.LENS_FACING_FRONT)
                lens = CameraCharacteristics.LENS_FACING_BACK;
        }
    }
    @Override protected void onResume() {
        super.onResume();
        active = true;
        if (worker == null) {
            worker = new HandlerThread("NabdhVideoCamera2");
            worker.start();
            handler = new Handler(worker.getLooper());
        }
        if (preview.isAvailable()) open();
        pipButton.setVisibility(Build.VERSION.SDK_INT >= 26 && option("video_pip") ?
                View.VISIBLE : View.GONE);
    }
    @Override protected void onPause() {
        if (!enteringPip && !(Build.VERSION.SDK_INT >= 26 && isInPictureInPictureMode())) {
            active = false;
            stopRecording();
            closeCamera();
            releaseWorker();
        }
        super.onPause();
    }
    @Override protected void onStop() {
        if (!enteringPip && !(Build.VERSION.SDK_INT >= 26 && isInPictureInPictureMode())) {
            active = false;
            stopRecording();
            closeCamera();
            releaseWorker();
        }
        super.onStop();
    }
    @Override protected void onDestroy() {
        active = false;
        stopRecording();
        closeCamera();
        releaseWorker();
        disk.shutdown(); // Final MediaStore commit may finish after UI closes.
        super.onDestroy();
    }
    @Override public void onPictureInPictureModeChanged(boolean inPip, Configuration config) {
        super.onPictureInPictureModeChanged(inPip, config);
        enteringPip = false;
        // Recording continues only while PiP remains visible.
    }
    private void releaseWorker() {
        if (worker != null) {
            worker.quitSafely();
            worker = null;
            handler = null;
        }
    }
    private void restart() {
        closeCamera();
        if (active && preview.isAvailable()) open();
    }
    private void open() {
        if (!active || opening || camera != null || handler == null || manager == null ||
                !preview.isAvailable()) return;
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.CAMERA}, PERMISSION);
            return;
        }
        try {
            String found = null;
            for (String id : manager.getCameraIdList()) {
                Integer direction = manager.getCameraCharacteristics(id).get(
                        CameraCharacteristics.LENS_FACING);
                if (direction != null && direction == lens) { found = id; break; }
            }
            if (found == null) throw new IllegalStateException("No matching video camera");
            cameraId = found;
            CameraCharacteristics info = manager.getCameraCharacteristics(found);
            Integer sensor = info.get(CameraCharacteristics.SENSOR_ORIENTATION);
            sensorOrientation = sensor == null ? 90 : sensor;
            StreamConfigurationMap map = info.get(
                    CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
            if (map == null || map.getOutputSizes(MediaRecorder.class) == null)
                throw new IllegalStateException("Video recording unsupported");
            Size[] sizes = map.getOutputSizes(MediaRecorder.class);
            long chosenArea = 0;
            for (Size size : sizes) {
                long area = (long) size.getWidth() * size.getHeight();
                // Stay within reliable H.264 1080p capability for this first release.
                if (area >= 640L * 480 && area <= 1920L * 1080 && area > chosenArea) {
                    chosenArea = area;
                    videoSize = size;
                }
            }
            if (chosenArea == 0) throw new IllegalStateException("No safe video resolution");
            int requested = NabdhHomePrefs.videoFps(this);
            Range<Integer>[] supported = info.get(
                    CameraCharacteristics.CONTROL_AE_AVAILABLE_TARGET_FPS_RANGES);
            frames = 30;
            fpsRange = null;
            if (supported != null) {
                int best = 0;
                for (Range<Integer> range : supported) {
                    int candidate = Math.min(requested, range.getUpper());
                    if (candidate >= range.getLower() && candidate > best) {
                        best = candidate;
                        fpsRange = range;
                    }
                }
                if (best > 0) frames = best;
            }
            eisAvailable = false;
            int[] modes = info.get(CameraCharacteristics.CONTROL_AVAILABLE_VIDEO_STABILIZATION_MODES);
            if (modes != null) for (int mode : modes) {
                if (mode == CaptureRequest.CONTROL_VIDEO_STABILIZATION_MODE_ON)
                    eisAvailable = true;
            }
            opening = true;
            final long token = generation;
            manager.openCamera(cameraId, new CameraDevice.StateCallback() {
                @Override public void onOpened(CameraDevice opened) {
                    if (generation != token || !active) { opened.close(); return; }
                    opening = false;
                    camera = opened;
                    createSession(false, token);
                }
                @Override public void onDisconnected(CameraDevice disconnected) {
                    disconnected.close();
                    if (generation == token) {
                        opening = false;
                        camera = null;
                        toast("Camera disconnected", "انقطع اتصال الكاميرا");
                    }
                }
                @Override public void onError(CameraDevice broken, int error) {
                    broken.close();
                    if (generation == token) {
                        opening = false;
                        camera = null;
                        toast("Camera unavailable", "الكاميرا غير متاحة");
                    }
                }
            }, handler);
        } catch (Exception e) {
            opening = false;
            closeCamera();
            toast("Camera2 video setup unavailable", "تعذّر إعداد فيديو Camera2");
        }
    }
    private void createSession(boolean forRecording, long token) {
        final long sessionToken = ++sessionGeneration;
        if (camera == null || !active || !preview.isAvailable() ||
                generation != token || handler == null) return;
        try {
            if (session != null) { session.close(); session = null; }
            if (previewSurface == null) {
                SurfaceTexture texture = preview.getSurfaceTexture();
                if (texture == null) throw new IllegalStateException("No preview texture");
                texture.setDefaultBufferSize(videoSize.getWidth(), videoSize.getHeight());
                previewSurface = new Surface(texture);
            }
            final Surface videoSurface = forRecording && recorder != null
                    ? recorder.getSurface() : null;
            CaptureRequest.Builder repeating = camera.createCaptureRequest(
                    forRecording ? CameraDevice.TEMPLATE_RECORD : CameraDevice.TEMPLATE_PREVIEW);
            repeating.addTarget(previewSurface);
            if (videoSurface != null) repeating.addTarget(videoSurface);
            repeating.set(CaptureRequest.CONTROL_AF_MODE,
                    CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_VIDEO);
            if (fpsRange != null) repeating.set(
                    CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE, fpsRange);
            if (eisAvailable && option("video_stabilize")) {
                repeating.set(CaptureRequest.CONTROL_VIDEO_STABILIZATION_MODE,
                        CaptureRequest.CONTROL_VIDEO_STABILIZATION_MODE_ON);
            }
            Surface[] targets = videoSurface == null ?
                    new Surface[]{previewSurface} :
                    new Surface[]{previewSurface, videoSurface};
            camera.createCaptureSession(Arrays.asList(targets),
                    new CameraCaptureSession.StateCallback() {
                        @Override public void onConfigured(CameraCaptureSession ready) {
                            if (token != generation || sessionToken != sessionGeneration
                                    || !active || camera == null) {
                                ready.close(); return;
                            }
                            session = ready;
                            try {
                                ready.setRepeatingRequest(repeating.build(), null, handler);
                                if (forRecording && recorder != null) {
                                    recorder.start();
                                    recording = true;
                                    configuring = false;
                                    runOnUiThread(() -> {
                                        recordButton.setText(local("Stop recording", "إيقاف التسجيل"));
                                        pipButton.setEnabled(option("video_pip"));
                                    });
                                }
                            } catch (Exception failed) {
                                configuring = false;
                                toast("Video recording could not start",
                                        "تعذر بدء تسجيل الفيديو");
                                stopRecording();
                            }
                        }
                        @Override public void onConfigureFailed(CameraCaptureSession bad) {
                            if (sessionToken != sessionGeneration) { bad.close(); return; }
                            configuring = false;
                            bad.close();
                            toast("Video session not supported", "جلسة الفيديو غير مدعومة");
                            stopRecording();
                        }
                    }, handler);
        } catch (Exception e) {
            configuring = false;
            toast("Video preview unavailable", "معاينة الفيديو غير متاحة");
            stopRecording();
        }
    }
    private void startRecording() {
        if (recording || configuring || camera == null || session == null) return;
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, PERMISSION);
            return;
        }
        try {
            temp = new File(getCacheDir(), "nabdh-video-" + System.currentTimeMillis() + ".mp4");
            recorder = new MediaRecorder();
            recorder.setAudioSource(MediaRecorder.AudioSource.MIC);
            recorder.setVideoSource(MediaRecorder.VideoSource.SURFACE);
            recorder.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4);
            recorder.setAudioEncoder(MediaRecorder.AudioEncoder.AAC);
            recorder.setAudioEncodingBitRate(96000);
            recorder.setAudioSamplingRate(44100);
            recorder.setVideoEncoder(MediaRecorder.VideoEncoder.H264);
            recorder.setVideoEncodingBitRate(videoSize.getWidth() >= 1920 ? 7_000_000 : 4_000_000);
            recorder.setVideoFrameRate(frames);
            recorder.setVideoSize(videoSize.getWidth(), videoSize.getHeight());
            // Fail safely after ten minutes or 512 MiB instead of filling
            // available storage on a long or abandoned recording.
            recorder.setMaxDuration(10 * 60 * 1000);
            recorder.setMaxFileSize(512L * 1024 * 1024);
            recorder.setOnInfoListener((mediaRecorder, what, extra) -> {
                if (what == MediaRecorder.MEDIA_RECORDER_INFO_MAX_DURATION_REACHED
                        || what == MediaRecorder.MEDIA_RECORDER_INFO_MAX_FILESIZE_REACHED) {
                    runOnUiThread(() -> {
                        if (recording) stopRecording();
                    });
                }
            });
            int degrees = getWindowManager().getDefaultDisplay().getRotation() * 90;
            recorder.setOrientationHint(lens == CameraCharacteristics.LENS_FACING_FRONT ?
                    (sensorOrientation + degrees) % 360 :
                    (sensorOrientation - degrees + 360) % 360);
            recorder.setOutputFile(temp.getAbsolutePath());
            recorder.prepare();
            configuring = true;
            createSession(true, generation);
        } catch (Exception e) {
            configuring = false;
            stopRecording();
            toast("Video encoder could not be started", "تعذر تشغيل ترميز الفيديو");
        }
    }
    private void stopRecording() {
        if (!recording && !configuring && recorder == null) return;
        final boolean completed = recording;
        recording = false;
        configuring = false;
        if (session != null) {
            try { session.stopRepeating(); } catch (CameraAccessException | IllegalStateException ignored) { }
            session.close();
            session = null;
        }
        if (recorder != null) {
            boolean saved = false;
            try {
                if (completed) { recorder.stop(); saved = true; }
            } catch (RuntimeException early) {
                toast("Recording too short; retry", "التسجيل قصير جدًا؛ أعد المحاولة");
            } finally {
                try { recorder.reset(); } catch (RuntimeException ignored) { }
                recorder.release();
                recorder = null;
            }
            final File captured = temp;
            temp = null;
            if (captured != null) {
                if (saved && captured.length() > 1024) {
                    try {
                        disk.execute(() -> persist(captured));
                    } catch (RejectedExecutionException backlog) {
                        captured.delete();
                        toast("Video storage is busy; retry later",
                                "التخزين مشغول بحفظ فيديوهات سابقة؛ أعد المحاولة");
                    }
                } else captured.delete();
            }
        }
        if (!isFinishing() && active && camera != null && preview.isAvailable()) {
            createSession(false, generation);
        }
        if (recordButton != null) runOnUiThread(() -> {
            recordButton.setText(local("Start recording", "بدء تسجيل الفيديو"));
            pipButton.setEnabled(false);
        });
    }
    private void persist(File captured) {
        String name = "NabdhVideo_" + System.currentTimeMillis() + ".mp4";
        Uri uri = null;
        // Commit only a non-empty, finalized file to public MediaStore.
        try {
            if (Build.VERSION.SDK_INT >= 29) {
                ContentValues values = new ContentValues();
                values.put(MediaStore.Video.Media.DISPLAY_NAME, name);
                values.put(MediaStore.Video.Media.MIME_TYPE, "video/mp4");
                values.put(MediaStore.Video.Media.RELATIVE_PATH,
                        Environment.DIRECTORY_MOVIES + "/NabdhGram");
                values.put(MediaStore.Video.Media.IS_PENDING, 1);
                uri = getContentResolver().insert(
                        MediaStore.Video.Media.EXTERNAL_CONTENT_URI, values);
                if (uri == null) throw new java.io.IOException("MediaStore video");
                try (FileInputStream in = new FileInputStream(captured);
                     OutputStream out = getContentResolver().openOutputStream(uri)) {
                    if (out == null) throw new java.io.IOException("Video output");
                    byte[] buffer = new byte[128 * 1024];
                    int n; while ((n = in.read(buffer)) != -1) out.write(buffer, 0, n);
                }
                ContentValues done = new ContentValues();
                done.put(MediaStore.Video.Media.IS_PENDING, 0);
                getContentResolver().update(uri, done, null, null);
            } else {
                File folder = new File(getExternalFilesDir(Environment.DIRECTORY_MOVIES), "NabdhGram");
                if (!folder.exists() && !folder.mkdirs())
                    throw new java.io.IOException("Video directory");
                File out = new File(folder, name);
                if (!captured.renameTo(out)) {
                    try (FileInputStream in = new FileInputStream(captured);
                         FileOutputStream dst = new FileOutputStream(out)) {
                        byte[] buf = new byte[128 * 1024];
                        int n; while ((n = in.read(buf)) != -1) dst.write(buf, 0, n);
                    }
                }
                uri = FileProvider.getUriForFile(this, getPackageName() + ".provider", out);
            }
            lastVideo = uri;
            if (!isFinishing()) runOnUiThread(() -> {
                shareButton.setEnabled(true);
                toast("Video saved; ready to share", "حُفظ الفيديو وأصبح جاهزًا للمشاركة");
            });
        } catch (Exception error) {
            if (uri != null && Build.VERSION.SDK_INT >= 29) {
                try { getContentResolver().delete(uri, null, null); }
                catch (RuntimeException ignored) { }
            }
            toast("Video could not be saved", "تعذر حفظ الفيديو");
        } finally {
            captured.delete();
        }
    }
    private void share() {
        Uri uri = lastVideo;
        if (uri == null) return;
        try {
            Intent send = new Intent(this, LaunchActivity.class);
            send.setAction(Intent.ACTION_SEND);
            send.setType("video/mp4");
            send.putExtra(Intent.EXTRA_STREAM, uri);
            send.setClipData(ClipData.newUri(getContentResolver(), "Nabdh Video", uri));
            send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            startActivity(send);
        } catch (RuntimeException e) {
            toast("Video sharing unavailable", "مشاركة الفيديو غير متاحة");
        }
    }
    private void startPip() {
        if (Build.VERSION.SDK_INT < 26 || !option("video_pip") || !recording) {
            toast("Start recording first", "ابدأ تسجيل الفيديو أولًا");
            return;
        }
        try {
            enteringPip = true;
            PictureInPictureParams params = new PictureInPictureParams.Builder()
                    .setAspectRatio(new Rational(videoSize.getWidth(), videoSize.getHeight()))
                    .build();
            if (!enterPictureInPictureMode(params)) enteringPip = false;
        } catch (RuntimeException failed) {
            enteringPip = false;
            toast("Picture-in-picture is unavailable on this device",
                    "العرض العائم PiP غير متاح على الجهاز");
        }
    }
    private void closeCamera() {
        generation++;
        sessionGeneration++;
        opening = false;
        configuring = false;
        if (session != null) { session.close(); session = null; }
        if (camera != null) { camera.close(); camera = null; }
        if (previewSurface != null) { previewSurface.release(); previewSurface = null; }
    }
    @Override public void onRequestPermissionsResult(int requestCode,
            String[] permissions, int[] results) {
        super.onRequestPermissionsResult(requestCode, permissions, results);
        if (requestCode != PERMISSION) return;
        boolean granted = results.length != 0;
        for (int value : results) granted &= value == PackageManager.PERMISSION_GRANTED;
        if (!granted) {
            toast("Camera and microphone permissions required for video",
                    "يحتاج الفيديو إلى إذنَي الكاميرا والميكروفون");
            return;
        }
        if (camera == null) open();
        else startRecording();
    }
}