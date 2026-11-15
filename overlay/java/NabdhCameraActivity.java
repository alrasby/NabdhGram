package org.telegram.ui;

import android.Manifest;
import android.app.Activity;
import android.content.ContentValues;
import android.content.Context;
import android.content.pm.PackageManager;
import android.graphics.ImageFormat;
import android.graphics.Rect;
import android.graphics.SurfaceTexture;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraDevice;
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
import android.widget.LinearLayout;
import android.widget.Toast;

import java.io.File;
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
    private ImageReader reader;
    private CaptureRequest.Builder repeating;
    private String cameraId;
    private int facing = CameraCharacteristics.LENS_FACING_BACK;
    private boolean torch;
    private float zoom = 1f;
    private float zoomMax = 1f;
    private Rect activeArray;
    private int sensorOrientation;
    private volatile boolean active;
    private volatile boolean takingPhoto;

    private Button control(String title, Runnable action) {
        Button result = new Button(this);
        result.setAllCaps(false);
        result.setText(title);
        result.setTextSize(12);
        result.setOnClickListener(v -> action.run());
        return result;
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        setTitle("Nabdh Camera2");
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        preview = new TextureView(this);
        page.addView(preview, new LinearLayout.LayoutParams(-1, 0, 1f));
        LinearLayout commands = new LinearLayout(this);
        commands.setGravity(Gravity.CENTER);
        commands.addView(control("↻", () -> {
            facing = facing == CameraCharacteristics.LENS_FACING_BACK
                     ? CameraCharacteristics.LENS_FACING_FRONT
                     : CameraCharacteristics.LENS_FACING_BACK;
            zoom = 1f;
            restartCamera();
        }));
        commands.addView(control("−", () -> {
            zoom = Math.max(1f, zoom / 1.3f);
            refreshRepeating();
        }));
        commands.addView(control("+", () -> {
            zoom = Math.min(zoomMax, zoom * 1.3f);
            refreshRepeating();
        }));
        commands.addView(control("Flash", () -> {
            torch = !torch;
            refreshRepeating();
        }));
        commands.addView(control("●", this::takePhoto));
        page.addView(commands, new LinearLayout.LayoutParams(-1, -2));
        setContentView(page);
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
        if (!active || manager == null || device != null || cameraHandler == null) return;
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
            reader = ImageReader.newInstance(size.getWidth(), size.getHeight(),
                    ImageFormat.JPEG, 2);
            reader.setOnImageAvailableListener(source -> {
                try (Image image = source.acquireLatestImage()) {
                    if (image == null) return;
                    ByteBuffer buffer = image.getPlanes()[0].getBuffer();
                    byte[] bytes = new byte[buffer.remaining()];
                    buffer.get(bytes);
                    savePhoto(bytes);
                } catch (Exception error) {
                    notifyUser("Photo could not be saved");
                } finally { takingPhoto = false; }
            }, cameraHandler);
            manager.openCamera(cameraId, new CameraDevice.StateCallback() {
                @Override public void onOpened(CameraDevice opened) {
                    if (!active) { opened.close(); return; }
                    device = opened;
                    createPreview();
                }
                @Override public void onDisconnected(CameraDevice opened) {
                    opened.close();
                    if (device == opened) device = null;
                }
                @Override public void onError(CameraDevice opened, int error) {
                    opened.close();
                    if (device == opened) device = null;
                    notifyUser("Camera unavailable (" + error + ")");
                }
            }, cameraHandler);
        } catch (Exception problem) {
            notifyUser("Camera unavailable on this device");
            closeCamera();
        }
    }

    private void createPreview() {
        if (!active || device == null || reader == null || !preview.isAvailable()) return;
        try {
            SurfaceTexture texture = preview.getSurfaceTexture();
            if (texture == null) return;
            texture.setDefaultBufferSize(1280, 720);
            Surface screen = new Surface(texture);
            repeating = device.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW);
            repeating.addTarget(screen);
            repeating.set(CaptureRequest.CONTROL_AF_MODE,
                    CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE);
            device.createCaptureSession(Arrays.asList(screen, reader.getSurface()),
                    new CameraCaptureSession.StateCallback() {
                        @Override public void onConfigured(CameraCaptureSession ready) {
                            if (!active || device == null) { ready.close(); return; }
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
        if (device == null || session == null || reader == null || takingPhoto) return;
        takingPhoto = true;
        try {
            CaptureRequest.Builder capture = device.createCaptureRequest(
                    CameraDevice.TEMPLATE_STILL_CAPTURE);
            capture.addTarget(reader.getSurface());
            capture.set(CaptureRequest.CONTROL_AF_MODE,
                    CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE);
            applySettings(capture);
            int degrees = getWindowManager().getDefaultDisplay().getRotation() * 90;
            // Surface ROTATION_0..3 are quarter turns.
            capture.set(CaptureRequest.JPEG_ORIENTATION,
                    facing == CameraCharacteristics.LENS_FACING_FRONT
                            ? (sensorOrientation + degrees) % 360
                            : (sensorOrientation - degrees + 360) % 360);
            session.capture(capture.build(), null, cameraHandler);
        } catch (Exception error) {
            takingPhoto = false;
            notifyUser("Capture failed");
        }
    }

    private void savePhoto(byte[] bytes) throws Exception {
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
        } else {
            File folder = new File(getExternalFilesDir(Environment.DIRECTORY_PICTURES), "NabdhGram");
            if (!folder.exists() && !folder.mkdirs()) throw new java.io.IOException("Directory");
            try (OutputStream stream = new FileOutputStream(new File(folder, name))) {
                stream.write(bytes);
            }
        }
        notifyUser("Saved: " + name);
    }

    private void notifyUser(String message) {
        runOnUiThread(() -> Toast.makeText(this, message, Toast.LENGTH_SHORT).show());
    }

    private void closeCamera() {
        if (session != null) { session.close(); session = null; }
        if (device != null) { device.close(); device = null; }
        if (reader != null) { reader.close(); reader = null; }
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
