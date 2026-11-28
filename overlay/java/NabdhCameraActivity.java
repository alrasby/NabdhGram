package org.telegram.ui;

import android.Manifest;
import android.app.Activity;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.content.ClipData;
import android.content.pm.PackageManager;
import android.graphics.ImageFormat;
import android.graphics.Rect;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Matrix;
import androidx.exifinterface.media.ExifInterface;
import android.graphics.SurfaceTexture;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CaptureFailure;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.params.StreamConfigurationMap;
import android.media.Image;
import android.media.ImageReader;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Looper;
import android.provider.MediaStore;
import android.util.Size;
import android.view.Gravity;
import android.view.Surface;
import android.view.TextureView;
import android.view.View;
import android.widget.Button;
import android.widget.SeekBar;
import androidx.core.content.FileProvider;
import android.widget.LinearLayout;
import android.widget.Toast;

import java.io.File;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/**
 * Independent Camera2 still-image tool. All camera resources are closed on
 * pause; it never changes Telegram's native composer/camera/call pipeline.
 */
public final class NabdhCameraActivity extends Activity {
    private static final int CAMERA_PERMISSION = 5101;
    private TextureView preview;
    private CameraManager manager;
    private HandlerThread worker;
    private Handler cameraHandler;
    private CameraDevice device;
    private CameraCaptureSession session;
    private Surface previewSurface;
    private ImageReader reader;
    private volatile boolean openingCamera;
    private boolean requestingPermission;
    private volatile long cameraGeneration;
    private CaptureRequest.Builder repeating;
    private String cameraId;
    private int facing = CameraCharacteristics.LENS_FACING_BACK;
    private boolean torch;
    private float zoom = 1f;
    private float zoomMax = 1f;
    private SeekBar zoomSlider;
    private boolean oisAvailable;
    private boolean hdrAvailable;
    private boolean noiseReductionAvailable;
    private boolean edgeProcessingAvailable;
    private boolean resolutionFallback;
    private Rect activeArray;
    private int sensorOrientation;
    private volatile boolean active;
    private volatile boolean takingPhoto;
    private volatile Uri lastPhotoUri;
    private volatile File lastPhotoFile;
    private Button sharePhoto;
    private Button shutterButton;
    private Button timerButton;
    private int timerSeconds;
    private int countdown;
    private final Handler timerHandler = new Handler(Looper.getMainLooper());
    private Runnable timerCallback;
    private final ThreadPoolExecutor photoShareWorker = new ThreadPoolExecutor(
            1, 1, 30, TimeUnit.SECONDS, new ArrayBlockingQueue<>(2));

    private int dp(float value) {
        return (int) (getResources().getDisplayMetrics().density * value + .5f);
    }

    private String local(String en, String ar) {
        return org.telegram.messenger.LocaleController.isRTL ? ar : en;
    }

    private Button control(String title, Runnable action) {
        Button result = new Button(this);
        result.setAllCaps(false);
        result.setText(title);
        result.setTextSize(12);
        result.setMinHeight((int) (48 * getResources().getDisplayMetrics().density + .5f));
        result.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteBlackText));
        org.telegram.ui.Components.NabdhToolUi.styleButton(this, result);
        result.setOnClickListener(v -> action.run());
        return result;
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        setTitle(local("Nabdh Camera2", "كاميرا نبض جرام"));
        if (cameraOption("camera_remember")) {
            facing = getSharedPreferences("nabdh_ui_personalization_v1", MODE_PRIVATE)
                    .getInt("camera_last_facing", CameraCharacteristics.LENS_FACING_BACK);
            if (facing != CameraCharacteristics.LENS_FACING_FRONT) {
                facing = CameraCharacteristics.LENS_FACING_BACK;
            }
        }
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setBackgroundColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundGray));
        page.setLayoutDirection(org.telegram.messenger.LocaleController.isRTL
                ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        preview = new TextureView(this);
        page.addView(preview, new LinearLayout.LayoutParams(-1, 0, 1f));
        // Four equally sized controls; the original five-button row was cropped.
        LinearLayout commands = new LinearLayout(this);
        commands.setGravity(Gravity.CENTER);
        commands.setPadding(dp(6), dp(4), dp(6), dp(4));
        Button switchCamera = control("↻", () -> {
            requestingPermission = false;
            cancelCountdown();
            facing = facing == CameraCharacteristics.LENS_FACING_BACK
                     ? CameraCharacteristics.LENS_FACING_FRONT
                     : CameraCharacteristics.LENS_FACING_BACK;
            zoom = 1f;
            resolutionFallback = false;
            if (cameraOption("camera_remember")) {
                getSharedPreferences("nabdh_ui_personalization_v1", MODE_PRIVATE)
                        .edit().putInt("camera_last_facing", facing).apply();
            }
            if (zoomSlider != null) zoomSlider.setProgress(0);
            restartCamera();
        });
        switchCamera.setContentDescription(local("Switch camera", "تبديل الكاميرا"));
        Button zoomOut = control("−", () -> {
            zoom = Math.max(1f, zoom / 1.3f);
            refreshRepeating();
        });
        zoomOut.setContentDescription(local("Zoom out", "تصغير"));
        Button zoomIn = control("+", () -> {
            zoom = Math.min(zoomMax, zoom * 1.3f);
            refreshRepeating();
        });
        zoomIn.setContentDescription(local("Zoom in", "تكبير"));
        Button flash = control(local("Flash", "الفلاش"), () -> {
            torch = !torch;
            refreshRepeating();
        });
        for (Button item : new Button[]{switchCamera, zoomOut, zoomIn, flash}) {
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, dp(48), 1f);
            lp.setMarginEnd(dp(3));
            commands.addView(item, lp);
        }
        page.addView(commands, new LinearLayout.LayoutParams(-1, dp(56)));
        zoomSlider = new SeekBar(this);
        zoomSlider.setMax(100);
        zoomSlider.setContentDescription(local("Camera zoom", "تكبير الكاميرا"));
        zoomSlider.setVisibility(cameraOption("camera_zoom_bar") ? View.VISIBLE : View.GONE);
        zoomSlider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(SeekBar bar, int progress, boolean user) {
                if (!user) return;
                zoom = 1f + (zoomMax - 1f) * progress / 100f;
                refreshRepeating();
            }
            @Override public void onStartTrackingTouch(SeekBar bar) {}
            @Override public void onStopTrackingTouch(SeekBar bar) {}
        });
        page.addView(zoomSlider, new LinearLayout.LayoutParams(-1, dp(40)));

        LinearLayout captureBar = new LinearLayout(this);
        captureBar.setGravity(Gravity.CENTER);
        captureBar.setPadding(0, dp(2), 0, dp(4));
        Button shutter = new Button(this);
        shutter.setAllCaps(false);
        shutter.setText("●");
        shutter.setTextSize(34);
        shutter.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteBlueText));
        shutter.setContentDescription(local("Capture photo", "التقاط صورة"));
        shutter.setMinHeight(0);
        shutter.setMinimumWidth(0);
        android.graphics.drawable.GradientDrawable ring =
                new android.graphics.drawable.GradientDrawable();
        ring.setShape(android.graphics.drawable.GradientDrawable.OVAL);
        ring.setColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhite));
        int accent = org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteBlueText);
        ring.setStroke(dp(3), accent);
        android.graphics.drawable.GradientDrawable mask =
                new android.graphics.drawable.GradientDrawable();
        mask.setShape(android.graphics.drawable.GradientDrawable.OVAL);
        mask.setColor(android.graphics.Color.WHITE);
        shutter.setBackground(new android.graphics.drawable.RippleDrawable(
                android.content.res.ColorStateList.valueOf(
                        android.graphics.Color.argb(54, android.graphics.Color.red(accent),
                                android.graphics.Color.green(accent),
                                android.graphics.Color.blue(accent))),
                ring, mask));
        shutterButton = shutter;
        shutter.setEnabled(false);
        shutter.setOnClickListener(v -> startTimedPhoto());
        timerButton = control(local("Timer off", "المؤقت مغلق"), () -> {
            cancelCountdown();
            timerSeconds = timerSeconds == 0 ? 3 : timerSeconds == 3 ? 10 : 0;
            updateTimerLabel();
        });
        timerButton.setContentDescription(local("Camera shutter timer: off, 3 or 10 seconds",
                "مؤقت كاميرا نبض: إيقاف أو 3 أو 10 ثوانٍ"));
        captureBar.addView(timerButton, new LinearLayout.LayoutParams(dp(96), dp(52)));
        captureBar.addView(shutter, new LinearLayout.LayoutParams(dp(72), dp(72)));
        captureBar.addView(new View(this), new LinearLayout.LayoutParams(dp(96), dp(52)));
        page.addView(captureBar, new LinearLayout.LayoutParams(-1, dp(80)));
        LinearLayout photoTools = new LinearLayout(this);
        photoTools.setGravity(Gravity.CENTER_VERTICAL);
        sharePhoto = control(local("Share last photo", "مشاركة آخر صورة"), this::shareLastPhoto);
        sharePhoto.setEnabled(false);
        photoTools.addView(sharePhoto, new LinearLayout.LayoutParams(0, dp(52), 1));
        Button gallery = control(local("My photos", "معرض صوري"), () ->
                startActivity(new Intent(this, NabdhCameraGalleryActivity.class)));
        gallery.setContentDescription(local("Browse Nabdh Camera photos",
                "تصفح صور كاميرا نبض الملتقطة"));
        photoTools.addView(gallery, new LinearLayout.LayoutParams(0, dp(52), 1));
        page.addView(photoTools, new LinearLayout.LayoutParams(-1, dp(56)));
        page.addView(control(local("Record video with Nabdh Camera2", "تسجيل فيديو بكاميرا نبض"), () ->
                startActivity(new Intent(this, NabdhVideoActivity.class))),
                new LinearLayout.LayoutParams(-1, dp(48)));
        page.addView(control(local("Camera settings", "إعدادات الكاميرا"), () -> {
            Intent options = new Intent(this, NabdhPersonalizeActivity.class);
            options.putExtra(NabdhPersonalizeActivity.EXTRA_SECTION, NabdhPersonalizeActivity.CAMERA);
            startActivity(options);
        }), new LinearLayout.LayoutParams(-1, dp(48)));
        org.telegram.ui.Components.NabdhToolUi.install(this, page,
                local("Nabdh Camera2", "كاميرا نبض جرام"));
        manager = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
        preview.setSurfaceTextureListener(new TextureView.SurfaceTextureListener() {
            @Override public void onSurfaceTextureAvailable(SurfaceTexture s, int w, int h) {
                startCamera();
            }
            @Override public void onSurfaceTextureSizeChanged(SurfaceTexture s, int w, int h) {}
            @Override public boolean onSurfaceTextureDestroyed(SurfaceTexture s) {
                closeCamera();
                return true;
            }
            @Override public void onSurfaceTextureUpdated(SurfaceTexture s) {}
        });
    }

    @Override protected void onResume() {
        super.onResume();
        active = true;
        worker = new HandlerThread("NabdhCamera2");
        worker.start();
        cameraHandler = new Handler(worker.getLooper());
        if (zoomSlider != null) {
            zoomSlider.setVisibility(cameraOption("camera_zoom_bar") ? View.VISIBLE : View.GONE);
        }
        if (preview.isAvailable()) startCamera();
    }

    @Override protected void onPause() {
        active = false;
        cancelCountdown();
        closeCamera();
        if (worker != null) {
            // Never block the UI waiting for camera JPEG or HAL callbacks.
            // closeCamera() already invalidates cameraGeneration and releases
            // the session, device, reader and preview surface. The old Looper
            // exits asynchronously after its queued callbacks finish.
            worker.quitSafely();
            worker = null;
            cameraHandler = null;
        }
        super.onPause();
    }

    private void restartCamera() {
        closeCamera();
        if (active && preview.isAvailable()) startCamera();
    }

    private void startCamera() {
        if (!active || !preview.isAvailable() || device != null || openingCamera || cameraHandler == null) return;
        if (manager == null) {
            notifyUser(local("Camera service unavailable", "خدمة الكاميرا غير متاحة"));
            return;
        }
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            if (!requestingPermission) {
                requestingPermission = true;
                requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION);
            }
            return;
        }
        try {
            String selected = null;
            for (String id : manager.getCameraIdList()) {
                CameraCharacteristics info = manager.getCameraCharacteristics(id);
                Integer lens = info.get(CameraCharacteristics.LENS_FACING);
                if (lens != null && lens == facing) { selected = id; break; }
            }
            if (selected == null && manager.getCameraIdList().length != 0)
                selected = manager.getCameraIdList()[0];
            if (selected == null) throw new IllegalStateException("No camera");
            cameraId = selected;
            CameraCharacteristics info = manager.getCameraCharacteristics(cameraId);
            Integer actualFacing = info.get(CameraCharacteristics.LENS_FACING);
            if (actualFacing != null) facing = actualFacing;
            Rect sensor = info.get(CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE);
            activeArray = sensor;
            Float max = info.get(CameraCharacteristics.SCALER_AVAILABLE_MAX_DIGITAL_ZOOM);
            zoomMax = max == null ? 1f : Math.max(1f, Math.min(8f, max));
            if (zoomSlider != null) runOnUiThread(() ->
                    zoomSlider.setProgress(Math.round(100f * (zoom - 1f) /
                            Math.max(.01f, zoomMax - 1f))));
            hdrAvailable = hasMode(info.get(CameraCharacteristics.CONTROL_AVAILABLE_SCENE_MODES),
                    CaptureRequest.CONTROL_SCENE_MODE_HDR);
            noiseReductionAvailable = hasMode(
                    info.get(CameraCharacteristics.NOISE_REDUCTION_AVAILABLE_NOISE_REDUCTION_MODES),
                    CaptureRequest.NOISE_REDUCTION_MODE_HIGH_QUALITY);
            edgeProcessingAvailable = hasMode(
                    info.get(CameraCharacteristics.EDGE_AVAILABLE_EDGE_MODES),
                    CaptureRequest.EDGE_MODE_HIGH_QUALITY);
            int[] oisModes = info.get(CameraCharacteristics.LENS_INFO_AVAILABLE_OPTICAL_STABILIZATION);
            oisAvailable = false;
            if (oisModes != null) for (int mode : oisModes) {
                if (mode == CaptureRequest.LENS_OPTICAL_STABILIZATION_MODE_ON) {
                    oisAvailable = true;
                    break;
                }
            }
            Integer orientation = info.get(CameraCharacteristics.SENSOR_ORIENTATION);
            sensorOrientation = orientation == null ? 90 : orientation;
            StreamConfigurationMap formats = info.get(
                    CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
            if (formats == null || formats.getOutputSizes(ImageFormat.JPEG) == null)
                throw new IllegalStateException("No JPEG output");
            // High quality means the actual maximum JPEG resolution in the
            // standard Camera2 stream configuration, not a 12/24 MP cap.
            // Include slow high-resolution outputs when the HAL advertises them.
            Size size = choosePhotoSize(formats, cameraOption("camera_quality")
                    && !resolutionFallback);
            if (size == null) throw new IllegalStateException("No supported JPEG size");
            Size previewSize = choosePreviewSize(formats.getOutputSizes(SurfaceTexture.class));
            if (previewSize == null) throw new IllegalStateException("No supported preview size");
            reader = ImageReader.newInstance(size.getWidth(), size.getHeight(),
                    ImageFormat.JPEG, 2);
            final long readerGeneration = cameraGeneration;
            reader.setOnImageAvailableListener(source -> {
                if (!active || readerGeneration != cameraGeneration) return;
                try (Image image = source.acquireLatestImage()) {
                    if (image == null || !active || readerGeneration != cameraGeneration) return;
                    ByteBuffer buffer = image.getPlanes()[0].getBuffer();
                    // Fail rather than allocate unbounded input on a faulty HAL.
                    if (buffer.remaining() > 96 * 1024 * 1024)
                        throw new java.io.IOException("Camera JPEG exceeds safe buffer");
                    byte[] bytes = new byte[buffer.remaining()];
                    buffer.get(bytes);
                    if (!active || readerGeneration != cameraGeneration) return;
                    final Uri saved = savePhoto(
                            facing == CameraCharacteristics.LENS_FACING_FRONT &&
                            cameraOption("camera_mirror") ? mirroredSelfie(bytes) : bytes);
                    runOnUiThread(() -> {
                        if (!active || readerGeneration != cameraGeneration) return;
                        lastPhotoUri = saved;
                        if (sharePhoto != null) sharePhoto.setEnabled(saved != null);
                    });
                } catch (Exception error) {
                    notifyUser("Photo could not be saved");
                } finally { takingPhoto = false; }
            }, cameraHandler);
            openingCamera = true;
            final long generation = cameraGeneration;
            manager.openCamera(cameraId, new CameraDevice.StateCallback() {
                @Override public void onOpened(CameraDevice opened) {
                    if (!active || generation != cameraGeneration) { opened.close(); return; }
                    openingCamera = false;
                    device = opened;
                    createPreview(generation, previewSize);
                }
                @Override public void onDisconnected(CameraDevice opened) {
                    opened.close();
                    if (generation != cameraGeneration) return;
                    onCameraUnavailable(generation, local("Camera disconnected", "انقطع اتصال الكاميرا"));
                }
                @Override public void onError(CameraDevice opened, int error) {
                    opened.close();
                    if (generation != cameraGeneration) return;
                    onCameraUnavailable(generation,
                            local("Camera unavailable", "الكاميرا غير متاحة") + " (" + error + ")");
                }
            }, cameraHandler);
        } catch (Exception problem) {
            notifyUser(local("Camera unavailable on this device", "الكاميرا غير متاحة على هذا الجهاز"));
            closeCamera();
        }
    }

    private void createPreview(long generation, Size previewSize) {
        if (!active || generation != cameraGeneration || device == null || reader == null
                || !preview.isAvailable()) return;
        try {
            SurfaceTexture texture = preview.getSurfaceTexture();
            if (texture == null) return;
            texture.setDefaultBufferSize(previewSize.getWidth(), previewSize.getHeight());
            Surface screen = new Surface(texture);
            previewSurface = screen;
            repeating = device.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW);
            repeating.addTarget(screen);
            repeating.set(CaptureRequest.CONTROL_AF_MODE,
                    CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE);
            device.createCaptureSession(Arrays.asList(screen, reader.getSurface()),
                    new CameraCaptureSession.StateCallback() {
                        @Override public void onConfigured(CameraCaptureSession ready) {
                            if (!active || generation != cameraGeneration || device == null) {
                                ready.close();
                                return;
                            }
                            session = ready;
                            try {
                                applySettings(repeating);
                                ready.setRepeatingRequest(repeating.build(), null, cameraHandler);
                                runOnUiThread(() -> {
                                    if (active && generation == cameraGeneration) shutterButton.setEnabled(true);
                                });
                            } catch (CameraAccessException | IllegalStateException | IllegalArgumentException failure) {
                                onCameraUnavailable(generation,
                                        local("Camera preview unavailable", "معاينة الكاميرا غير متاحة"));
                            }
                        }
                        @Override public void onConfigureFailed(CameraCaptureSession failed) {
                            failed.close();
                            if (active && generation == cameraGeneration
                                    && cameraOption("camera_quality") && !resolutionFallback) {
                                resolutionFallback = true;
                                notifyUser(local("Maximum resolution unsupported in preview; "
                                        + "using a compatible photo size",
                                        "تعذرت معاينة أقصى دقة؛ سيتم استخدام دقة متوافقة"));
                                runOnUiThread(() -> {
                                    if (active && generation == cameraGeneration) restartCamera();
                                });
                            } else {
                                onCameraUnavailable(generation,
                                        local("Camera preview failed", "فشلت معاينة الكاميرا"));
                            }
                        }
                    }, cameraHandler);
        } catch (Exception failure) {
            onCameraUnavailable(generation,
                    local("Camera preview unavailable", "معاينة الكاميرا غير متاحة"));
        }
    }

    private void applySettings(CaptureRequest.Builder builder) {
        if (activeArray != null && zoom > 1f) {
            int width = Math.max(1, (int) (activeArray.width() / zoom));
            int height = Math.max(1, (int) (activeArray.height() / zoom));
            int left = activeArray.centerX() - width / 2;
            int top = activeArray.centerY() - height / 2;
            builder.set(CaptureRequest.SCALER_CROP_REGION,
                    new Rect(left, top, left + width, top + height));
        } else if (activeArray != null) {
            builder.set(CaptureRequest.SCALER_CROP_REGION, activeArray);
        }
        if (oisAvailable && cameraOption("camera_stabilize")) {
            builder.set(CaptureRequest.LENS_OPTICAL_STABILIZATION_MODE,
                    CaptureRequest.LENS_OPTICAL_STABILIZATION_MODE_ON);
        }
        builder.set(CaptureRequest.FLASH_MODE, torch
                ? CaptureRequest.FLASH_MODE_TORCH : CaptureRequest.FLASH_MODE_OFF);
    }

    private void refreshRepeating() {
        try {
            if (session != null && repeating != null) {
                applySettings(repeating);
                session.setRepeatingRequest(repeating.build(), null, cameraHandler);
            }
        } catch (CameraAccessException | IllegalStateException ignored) {
            notifyUser("Camera controls unavailable");
        }
    }

    private void updateTimerLabel() {
        if (timerButton == null) return;
        timerButton.setText(timerSeconds == 0 ? local("Timer off", "المؤقت مغلق")
                : (timerSeconds + local(" sec", " ثوانٍ")));
    }
    private void cancelCountdown() {
        if (timerCallback != null) timerHandler.removeCallbacks(timerCallback);
        timerCallback = null;
        countdown = 0;
        if (shutterButton != null) shutterButton.setText("●");
        updateTimerLabel();
    }
    private void startTimedPhoto() {
        if (takingPhoto) return;
        if (timerCallback != null) {
            cancelCountdown();
            return;
        }
        if (timerSeconds == 0) {
            takePhoto();
            return;
        }
        if (device == null || session == null || reader == null) {
            notifyUser(local("Camera is not ready", "الكاميرا ليست جاهزة بعد"));
            return;
        }
        final long generation = cameraGeneration;
        countdown = timerSeconds;
        timerCallback = new Runnable() {
            @Override public void run() {
                if (!active || generation != cameraGeneration) {
                    cancelCountdown();
                    return;
                }
                if (countdown <= 0) {
                    cancelCountdown();
                    takePhoto();
                    return;
                }
                if (shutterButton != null) shutterButton.setText(Integer.toString(countdown));
                countdown--;
                timerHandler.postDelayed(this, 1000);
            }
        };
        timerCallback.run();
    }

    private void takePhoto() {
        if (takingPhoto) return;
        if (device == null || session == null || reader == null) {
            notifyUser(local("Camera is not ready", "الكاميرا ليست جاهزة بعد"));
            return;
        }
        takingPhoto = true;
        try {
            CaptureRequest.Builder capture = device.createCaptureRequest(
                    CameraDevice.TEMPLATE_STILL_CAPTURE);
            capture.addTarget(reader.getSurface());
            capture.set(CaptureRequest.CONTROL_AF_MODE,
                    CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE);
            applySettings(capture);
            applyPhotoProcessing(capture);
            if (cameraOption("camera_quality")) {
                capture.set(CaptureRequest.JPEG_QUALITY, (byte) 100);
            }
            int degrees = getWindowManager().getDefaultDisplay().getRotation() * 90;
            // Surface ROTATION_0..3 are quarter turns.
            capture.set(CaptureRequest.JPEG_ORIENTATION,
                    facing == CameraCharacteristics.LENS_FACING_FRONT
                            ? (sensorOrientation + degrees) % 360
                            : (sensorOrientation - degrees + 360) % 360);
            session.capture(capture.build(), new CameraCaptureSession.CaptureCallback() {
                @Override public void onCaptureFailed(CameraCaptureSession current,
                        CaptureRequest request, CaptureFailure failure) {
                    takingPhoto = false;
                    notifyUser(local("Capture failed; retry", "فشل الالتقاط؛ أعد المحاولة"));
                }
                @Override public void onCaptureSequenceAborted(CameraCaptureSession current,
                        int sequenceId) {
                    takingPhoto = false;
                }
            }, cameraHandler);
        } catch (Exception error) {
            takingPhoto = false;
            notifyUser("Capture failed");
        }
    }

    private static Size choosePreviewSize(Size[] supported) {
        if (supported == null || supported.length == 0) return null;
        Size closest = null;
        long minimumDistance = Long.MAX_VALUE;
        for (Size candidate : supported) {
            long pixels = (long) candidate.getWidth() * candidate.getHeight();
            long distance = Math.abs(pixels - 1280L * 720L);
            if (distance < minimumDistance) {
                minimumDistance = distance;
                closest = candidate;
            }
        }
        return closest;
    }

    private static boolean hasMode(int[] supported, int requested) {
        if (supported == null) return false;
        for (int mode : supported) if (mode == requested) return true;
        return false;
    }

    private static Size choosePhotoSize(StreamConfigurationMap map, boolean maximum) {
        Size[] standard = map.getOutputSizes(ImageFormat.JPEG);
        if (standard == null || standard.length == 0) return null;
        Size chosen = null;
        if (maximum) {
            for (Size size : standard) {
                if (chosen == null || pixels(size) > pixels(chosen)) chosen = size;
            }
            if (Build.VERSION.SDK_INT >= 23) {
                try {
                    Size[] highRes = map.getHighResolutionOutputSizes(ImageFormat.JPEG);
                    if (highRes != null) for (Size size : highRes) {
                        if (pixels(size) > pixels(chosen)) chosen = size;
                    }
                } catch (IllegalArgumentException ignored) {
                    // OEM implementation does not expose a high-res list.
                }
            }
            return chosen;
        }
        // Fast fallback roughly 12 MP, or smallest native size above it.
        for (Size size : standard) {
            if (pixels(size) <= 12_000_000L &&
                    (chosen == null || pixels(size) > pixels(chosen))) chosen = size;
        }
        if (chosen != null) return chosen;
        for (Size size : standard) {
            if (chosen == null || pixels(size) < pixels(chosen)) chosen = size;
        }
        return chosen;
    }
    private static long pixels(Size size) {
        return (long) size.getWidth() * size.getHeight();
    }

    /** Vendor Camera2 ISP processing, not an independent or trained AI model. */
    private void applyPhotoProcessing(CaptureRequest.Builder capture) {
        if (!cameraOption("camera_smart_processing")) return;
        if (hdrAvailable) {
            capture.set(CaptureRequest.CONTROL_MODE, CaptureRequest.CONTROL_MODE_USE_SCENE_MODE);
            capture.set(CaptureRequest.CONTROL_SCENE_MODE,
                    CaptureRequest.CONTROL_SCENE_MODE_HDR);
        }
        if (noiseReductionAvailable)
            capture.set(CaptureRequest.NOISE_REDUCTION_MODE,
                    CaptureRequest.NOISE_REDUCTION_MODE_HIGH_QUALITY);
        if (edgeProcessingAvailable)
            capture.set(CaptureRequest.EDGE_MODE, CaptureRequest.EDGE_MODE_HIGH_QUALITY);
    }

    private boolean cameraOption(String key) {
        return org.telegram.ui.Components.NabdhHomePrefs.enabled(this, key);
    }

    /** Lossless mirror via JPEG EXIF metadata, preserving all source pixels.
     * Some external viewers may ignore EXIF orientation; never resample pixels
     * and silently discard the high-resolution result.
     */
    private byte[] mirroredSelfie(byte[] jpeg) throws Exception {
        if (jpeg.length > 64 * 1024 * 1024) {
            notifyUser(local("Large selfie saved without mirroring to preserve quality",
                    "حُفظت صورة السيلفي الكبيرة دون عكس حفاظًا على الجودة"));
            return jpeg;
        }
        File temp = File.createTempFile("nabdh-mirror-", ".jpg", getCacheDir());
        try {
            try (FileOutputStream out = new FileOutputStream(temp)) {
                out.write(jpeg);
            }
            ExifInterface exif = new ExifInterface(temp);
            exif.flipHorizontally();
            exif.saveAttributes();
            if (temp.length() > 96L * 1024 * 1024)
                throw new java.io.IOException("JPEG exceeded local processing limit");
            try (FileInputStream input = new FileInputStream(temp)) {
                ByteArrayOutputStream copy = new ByteArrayOutputStream((int) temp.length());
                byte[] block = new byte[16384];
                int n;
                while ((n = input.read(block)) >= 0) copy.write(block, 0, n);
                return copy.toByteArray();
            }
        } catch (Exception unsupported) {
            notifyUser(local("Mirroring unavailable; original photo saved",
                    "تعذر العكس؛ حُفظت الصورة الأصلية"));
            return jpeg;
        } finally {
            temp.delete();
        }
    }

    private Uri savePhoto(byte[] bytes) throws Exception {
        // No public MediaStore insertion: only NabdhGram's private directory.
        File original = NabdhCameraFiles.saveCapture(this, bytes);
        lastPhotoFile = original;
        notifyUser(local("Photo saved privately in Nabdh Camera",
                "حُفظت الصورة داخل كاميرا نبض فقط"));
        return NabdhCameraFiles.uri(this, original);
    }

    private void shareLastPhoto() {
        File file = lastPhotoFile;
        if (file == null) {
            notifyUser(local("Capture a photo first", "التقط صورة أولًا"));
            return;
        }
        if (sharePhoto != null) sharePhoto.setEnabled(false);
        try {
            photoShareWorker.execute(() -> {
                try {
                    // Removes EXIF GPS/XMP in a TEMP COPY, leaving private
                    // original and its original pixel encoding untouched.
                    Uri safe = NabdhCameraFiles.sanitizedShare(this, file);
                    runOnUiThread(() -> {
                        if (isFinishing() || isDestroyed()) return;
                        try {
                            Intent send = new Intent(this, LaunchActivity.class);
                            send.setAction(Intent.ACTION_SEND);
                            send.setType("image/jpeg");
                            send.putExtra(Intent.EXTRA_STREAM, safe);
                            send.setClipData(ClipData.newUri(getContentResolver(),
                                    "NabdhGram sanitized photo", safe));
                            send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                            startActivity(send);
                        } catch (RuntimeException failed) {
                            notifyUser(local("Photo sharing is unavailable",
                                    "تعذرت مشاركة الصورة"));
                        } finally {
                            if (sharePhoto != null) sharePhoto.setEnabled(true);
                        }
                    });
                } catch (Exception failClosed) {
                    runOnUiThread(() -> {
                        if (sharePhoto != null) sharePhoto.setEnabled(true);
                        notifyUser(local("Could not remove metadata. Original was NOT shared.",
                                "تعذرت إزالة البيانات الوصفية؛ لم تُشارك الصورة الأصلية."));
                    });
                }
            });
        } catch (RejectedExecutionException overloaded) {
            if (sharePhoto != null) sharePhoto.setEnabled(true);
            notifyUser(local("Photo processing is busy", "معالجة الصورة مشغولة"));
        }
    }

    private void notifyUser(String message) {
        runOnUiThread(() -> Toast.makeText(this, message, Toast.LENGTH_SHORT).show());
    }

    private void onCameraUnavailable(long generation, String message) {
        runOnUiThread(() -> {
            if (!active || generation != cameraGeneration) return;
            cancelCountdown();
            closeCamera();
            notifyUser(message);
        });
    }

    private void closeCamera() {
        if (shutterButton != null) shutterButton.setEnabled(false);
        cameraGeneration++;
        openingCamera = false;
        if (session != null) { session.close(); session = null; }
        if (device != null) { device.close(); device = null; }
        if (reader != null) { reader.close(); reader = null; }
        if (previewSurface != null) { previewSurface.release(); previewSurface = null; }
        repeating = null;
        takingPhoto = false;
    }

    @Override protected void onDestroy() {
        cancelCountdown();
        photoShareWorker.shutdownNow();
        super.onDestroy();
    }

    @Override public void onRequestPermissionsResult(
            int requestCode, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(requestCode, permissions, results);
        if (requestCode != CAMERA_PERMISSION) return;
        if (results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED) {
            requestingPermission = false;
            startCamera();
        } else {
            // Keep the request suppressed if onResume follows the denial.
            notifyUser(local("Camera permission is required", "يلزم السماح باستخدام الكاميرا"));
        }
    }
}
