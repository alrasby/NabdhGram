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
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;

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
    private volatile long cameraGeneration;
    private CaptureRequest.Builder repeating;
    private String cameraId;
    private int facing = CameraCharacteristics.LENS_FACING_BACK;
    private boolean torch;
    private float zoom = 1f;
    private float zoomMax = 1f;
    private SeekBar zoomSlider;
    private boolean oisAvailable;
    private Rect activeArray;
    private int sensorOrientation;
    private volatile boolean active;
    private volatile boolean takingPhoto;
    private volatile Uri lastPhotoUri;
    private Button sharePhoto;

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
            facing = facing == CameraCharacteristics.LENS_FACING_BACK
                     ? CameraCharacteristics.LENS_FACING_FRONT
                     : CameraCharacteristics.LENS_FACING_BACK;
            zoom = 1f;
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
        shutter.setOnClickListener(v -> takePhoto());
        captureBar.addView(shutter, new LinearLayout.LayoutParams(dp(72), dp(72)));
        page.addView(captureBar, new LinearLayout.LayoutParams(-1, dp(80)));
        sharePhoto = control(local("Share captured photo in NabdhGram",
                "إرسال الصورة الملتقطة في نبض جرام"), this::shareLastPhoto);
        sharePhoto.setEnabled(false);
        page.addView(sharePhoto, new LinearLayout.LayoutParams(-1, -2));
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
        closeCamera();
        if (worker != null) {
            worker.quitSafely();
            try { worker.join(1500); } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt();
            }
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
        if (!active || manager == null || device != null || openingCamera || cameraHandler == null) return;
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION);
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
            Rect sensor = info.get(CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE);
            activeArray = sensor;
            Float max = info.get(CameraCharacteristics.SCALER_AVAILABLE_MAX_DIGITAL_ZOOM);
            zoomMax = max == null ? 1f : Math.max(1f, Math.min(8f, max));
            if (zoomSlider != null) runOnUiThread(() ->
                    zoomSlider.setProgress(Math.round(100f * (zoom - 1f) /
                            Math.max(.01f, zoomMax - 1f))));
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
            Size[] output = formats.getOutputSizes(ImageFormat.JPEG);
            Size size = Collections.max(Arrays.asList(output), (a, b) ->
                    Long.compare((long) a.getWidth() * a.getHeight(),
                                 (long) b.getWidth() * b.getHeight()));
            // Avoid excessive memory allocation on 50+ MP sensors.
            for (Size option : output) {
                long area = (long) option.getWidth() * option.getHeight();
                if (area >= 1920L * 1080 && area <= 12_000_000L &&
                    area > (long) size.getWidth() * size.getHeight() / 8)
                    size = option;
            }
            if (cameraOption("camera_quality")) {
                for (Size option : output) {
                    long pixels = (long) option.getWidth() * option.getHeight();
                    long currentPixels = (long) size.getWidth() * size.getHeight();
                    long safeLimit = facing == CameraCharacteristics.LENS_FACING_FRONT &&
                            cameraOption("camera_mirror") ? 10_000_000L : 24_000_000L;
                    if (pixels <= safeLimit &&
                            (currentPixels > safeLimit || pixels > currentPixels)) size = option;
                }
            }
            reader = ImageReader.newInstance(size.getWidth(), size.getHeight(),
                    ImageFormat.JPEG, 2);
            reader.setOnImageAvailableListener(source -> {
                try (Image image = source.acquireLatestImage()) {
                    if (image == null) return;
                    ByteBuffer buffer = image.getPlanes()[0].getBuffer();
                    byte[] bytes = new byte[buffer.remaining()];
                    buffer.get(bytes);
                    final Uri saved = savePhoto(
                            facing == CameraCharacteristics.LENS_FACING_FRONT &&
                            cameraOption("camera_mirror") ? mirroredSelfie(bytes) : bytes);
                    runOnUiThread(() -> {
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
                    createPreview(generation);
                }
                @Override public void onDisconnected(CameraDevice opened) {
                    opened.close();
                    if (generation != cameraGeneration) return;
                    openingCamera = false;
                    if (device == opened) device = null;
                    notifyUser(local("Camera disconnected", "انقطع اتصال الكاميرا"));
                }
                @Override public void onError(CameraDevice opened, int error) {
                    opened.close();
                    if (generation != cameraGeneration) return;
                    openingCamera = false;
                    if (device == opened) device = null;
                    notifyUser(local("Camera unavailable", "الكاميرا غير متاحة") + " (" + error + ")");
                }
            }, cameraHandler);
        } catch (Exception problem) {
            notifyUser("Camera unavailable on this device");
            closeCamera();
        }
    }

    private void createPreview(long generation) {
        if (!active || generation != cameraGeneration || device == null || reader == null
                || !preview.isAvailable()) return;
        try {
            SurfaceTexture texture = preview.getSurfaceTexture();
            if (texture == null) return;
            texture.setDefaultBufferSize(1280, 720);
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
                            refreshRepeating();
                        }
                        @Override public void onConfigureFailed(CameraCaptureSession failed) {
                            notifyUser("Camera preview failed");
                        }
                    }, cameraHandler);
        } catch (Exception failure) {
            notifyUser("Camera preview unavailable");
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

    private boolean cameraOption(String key) {
        return org.telegram.ui.Components.NabdhHomePrefs.enabled(this, key);
    }

    /** Mirror only explicitly selected front-camera images, never chat media.
     * Decode downsampled JPEGs to avoid multi-megapixel OOM on older devices. */
    private byte[] mirroredSelfie(byte[] jpeg) throws Exception {
        BitmapFactory.Options bounds = new BitmapFactory.Options();
        bounds.inJustDecodeBounds = true;
        BitmapFactory.decodeByteArray(jpeg, 0, jpeg.length, bounds);
        if (bounds.outWidth <= 0 || bounds.outHeight <= 0)
            throw new java.io.IOException("Invalid selfie JPEG");
        BitmapFactory.Options options = new BitmapFactory.Options();
        options.inSampleSize = 1;
        while ((long) bounds.outWidth * bounds.outHeight /
                (options.inSampleSize * options.inSampleSize) > 6_000_000L) {
            options.inSampleSize *= 2;
        }
        Bitmap bitmap = BitmapFactory.decodeByteArray(jpeg, 0, jpeg.length, options);
        if (bitmap == null) throw new java.io.IOException("Selfie decoding failed");
        try {
            ExifInterface exif = new ExifInterface(new ByteArrayInputStream(jpeg));
            int orientation = exif.getAttributeInt(ExifInterface.TAG_ORIENTATION,
                    ExifInterface.ORIENTATION_NORMAL);
            Matrix transform = new Matrix();
            if (orientation == ExifInterface.ORIENTATION_ROTATE_90) transform.postRotate(90);
            else if (orientation == ExifInterface.ORIENTATION_ROTATE_180) transform.postRotate(180);
            else if (orientation == ExifInterface.ORIENTATION_ROTATE_270) transform.postRotate(270);
            transform.postScale(-1, 1);
            Bitmap flipped = Bitmap.createBitmap(bitmap, 0, 0,
                    bitmap.getWidth(), bitmap.getHeight(), transform, true);
            try {
                ByteArrayOutputStream output = new ByteArrayOutputStream(jpeg.length);
                if (!flipped.compress(Bitmap.CompressFormat.JPEG,
                        cameraOption("camera_quality") ? 100 : 95, output))
                    throw new java.io.IOException("Selfie JPEG encoding failed");
                return output.toByteArray();
            } finally {
                if (flipped != bitmap) flipped.recycle();
            }
        } finally {
            bitmap.recycle();
        }
    }

    private Uri savePhoto(byte[] bytes) throws Exception {
        String name = "NabdhCamera_" + System.currentTimeMillis() + ".jpg";
        if (Build.VERSION.SDK_INT >= 29) {
            ContentValues values = new ContentValues();
            values.put(MediaStore.Images.Media.DISPLAY_NAME, name);
            values.put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg");
            values.put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/NabdhGram");
            values.put(MediaStore.Images.Media.IS_PENDING, 1);
            Uri uri = getContentResolver().insert(
                    MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values);
            if (uri == null) throw new java.io.IOException("MediaStore");
            boolean good = false;
            try (OutputStream stream = getContentResolver().openOutputStream(uri)) {
                if (stream == null) throw new java.io.IOException("Output stream");
                stream.write(bytes);
                good = true;
            } finally {
                if (!good) getContentResolver().delete(uri, null, null);
            }
            ContentValues completed = new ContentValues();
            completed.put(MediaStore.Images.Media.IS_PENDING, 0);
            getContentResolver().update(uri, completed, null, null);
            notifyUser("Saved: " + name);
            return uri;
        } else {
            File folder = new File(getExternalFilesDir(Environment.DIRECTORY_PICTURES), "NabdhGram");
            if (!folder.exists() && !folder.mkdirs()) throw new java.io.IOException("Directory");
            File photo = new File(folder, name);
            try (OutputStream stream = new FileOutputStream(photo)) {
                stream.write(bytes);
            }
            // Telegram's existing manifest declares its own FileProvider.
            // Never expose file:// paths on Android 24+.
            Uri shared = FileProvider.getUriForFile(this,
                    getPackageName() + ".provider", photo);
            notifyUser("Saved: " + name);
            return shared;
        }
    }

    private void shareLastPhoto() {
        Uri uri = lastPhotoUri;
        if (uri == null) {
            notifyUser(local("Capture a photo first", "التقط صورة أولًا"));
            return;
        }
        try {
            // Same-app ACTION_SEND enters Telegram's native send/media flow.
            // Do not bypass Telegram's existing recipient and upload logic.
            Intent intent = new Intent(this, LaunchActivity.class);
            intent.setAction(Intent.ACTION_SEND);
            intent.setType("image/jpeg");
            intent.putExtra(Intent.EXTRA_STREAM, uri);
            intent.setClipData(ClipData.newUri(getContentResolver(),
                    "NabdhGram photo", uri));
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            startActivity(intent);
        } catch (RuntimeException error) {
            notifyUser(local("Could not open NabdhGram photo sharing",
                    "تعذّر فتح مشاركة الصورة في نبض جرام"));
        }
    }

    private void notifyUser(String message) {
        runOnUiThread(() -> Toast.makeText(this, message, Toast.LENGTH_SHORT).show());
    }

    private void closeCamera() {
        cameraGeneration++;
        openingCamera = false;
        if (session != null) { session.close(); session = null; }
        if (device != null) { device.close(); device = null; }
        if (reader != null) { reader.close(); reader = null; }
        if (previewSurface != null) { previewSurface.release(); previewSurface = null; }
        repeating = null;
        takingPhoto = false;
    }

    @Override public void onRequestPermissionsResult(
            int requestCode, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(requestCode, permissions, results);
        if (requestCode == CAMERA_PERMISSION && results.length > 0
                && results[0] == PackageManager.PERMISSION_GRANTED) startCamera();
        else if (requestCode == CAMERA_PERMISSION) notifyUser("Camera permission is required");
    }
}
