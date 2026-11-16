package org.telegram.ui;

import android.content.Context;
import android.net.Uri;
import androidx.core.content.FileProvider;
import androidx.exifinterface.media.ExifInterface;
import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.Arrays;
import java.util.Comparator;
import java.util.UUID;

/** App-private Nabdh Camera originals. Never writes to public MediaStore. */
public final class NabdhCameraFiles {
    private static final String ALBUM = "nabdh_camera";
    private static final String SHARES = "nabdh_private_share";
    private static final String PHOTO_PREFIX = "NabdhCamera_";
    private NabdhCameraFiles() {}

    public static File photoDirectory(Context context) throws IOException {
        File dir = new File(context.getFilesDir(), ALBUM);
        if (!dir.isDirectory() && !dir.mkdirs()) {
            throw new IOException("Could not create private photo album");
        }
        return dir;
    }

    public static File newPhoto(Context context) throws IOException {
        return new File(photoDirectory(context),
                PHOTO_PREFIX + System.currentTimeMillis() + "_"
                        + UUID.randomUUID().toString().replace("-", "") + ".jpg");
    }

    public static File photo(Context context, String name) throws IOException {
        if (name == null || !name.matches("NabdhCamera_[A-Za-z0-9_-]+\\.jpg")) {
            throw new IOException("Invalid Nabdh camera photo identifier");
        }
        File dir = photoDirectory(context).getCanonicalFile();
        File found = new File(dir, name).getCanonicalFile();
        if (!dir.equals(found.getParentFile()) || !found.isFile()) {
            throw new IOException("Photo not found in private album");
        }
        return found;
    }

    public static File[] recent(Context context) throws IOException {
        File[] all = photoDirectory(context).listFiles(file -> file.isFile()
                && file.getName().matches("NabdhCamera_[A-Za-z0-9_-]+\\.jpg"));
        if (all == null) return new File[0];
        Arrays.sort(all, Comparator.comparingLong(File::lastModified).reversed());
        return all.length > 400 ? Arrays.copyOf(all, 400) : all;
    }

    public static Uri uri(Context context, File file) {
        return FileProvider.getUriForFile(context,
                context.getPackageName() + ".provider", file);
    }

    public static File saveCapture(Context context, byte[] jpeg) throws IOException {
        if (jpeg == null || jpeg.length < 4 || jpeg[0] != (byte) 0xff
                || jpeg[1] != (byte) 0xd8) {
            throw new IOException("Invalid camera JPEG");
        }
        File target = newPhoto(context);
        boolean complete = false;
        try {
            try (OutputStream out = new BufferedOutputStream(new FileOutputStream(target))) {
                out.write(jpeg);
            }
            complete = true;
            return target;
        } finally {
            if (!complete) target.delete();
        }
    }

    private static File privateShareDir(Context context) throws IOException {
        File root = new File(context.getCacheDir(), SHARES);
        if (!root.isDirectory() && !root.mkdirs()) {
            throw new IOException("Could not prepare private share cache");
        }
        return root;
    }

    /** Delete ONLY our old temporary share files, never captured originals. */
    private static void cleanup(Context context) throws IOException {
        File[] cache = privateShareDir(context).listFiles();
        if (cache == null) return;
        long cutoff = System.currentTimeMillis() - 24L * 60 * 60 * 1000;
        for (File file : cache) {
            if (file.isFile() && file.getName().startsWith("share_")
                    && file.lastModified() < cutoff) file.delete();
        }
    }

    /** Lossless JPEG metadata scrub: retains encoded image data and optional
     * ICC color profile, but never copies Exif, XMP, GPS or Photoshop markers.
     * Preserve ONLY original pixel orientation in a fresh, empty Exif block.
     * Fail closed: callers must not fall back to sharing the original.
     */
    public static Uri sanitizedShare(Context context, File original) throws IOException {
        File checked = photo(context, original.getName());
        cleanup(context);
        File out = new File(privateShareDir(context),
                "share_" + UUID.randomUUID().toString().replace("-", "") + ".jpg");
        boolean complete = false;
        try {
            int orientation = new ExifInterface(checked).getAttributeInt(
                    ExifInterface.TAG_ORIENTATION, ExifInterface.ORIENTATION_NORMAL);
            try (InputStream input = new BufferedInputStream(new FileInputStream(checked));
                 OutputStream writer = new BufferedOutputStream(new FileOutputStream(out))) {
                removeMetadata(input, writer);
            }
            if (orientation != ExifInterface.ORIENTATION_NORMAL) {
                ExifInterface clean = new ExifInterface(out);
                clean.setAttribute(ExifInterface.TAG_ORIENTATION, Integer.toString(orientation));
                clean.saveAttributes();
            }
            if (out.length() < 4) throw new IOException("Empty scrubbed photo");
            ExifInterface check = new ExifInterface(out);
            if (check.getAttribute(ExifInterface.TAG_GPS_LATITUDE) != null ||
                    check.getAttribute(ExifInterface.TAG_GPS_LONGITUDE) != null ||
                    check.getAttribute(ExifInterface.TAG_GPS_ALTITUDE) != null) {
                throw new IOException("Share still contains geolocation metadata");
            }
            complete = true;
            return uri(context, out);
        } finally {
            if (!complete) out.delete();
        }
    }

    private static int required(InputStream input) throws IOException {
        int value = input.read();
        if (value == -1) throw new IOException("Truncated JPEG metadata");
        return value;
    }
    private static void copy(InputStream in, OutputStream out, long n)
            throws IOException {
        byte[] chunk = new byte[16 * 1024];
        while (n > 0) {
            int read = in.read(chunk, 0, (int) Math.min(chunk.length, n));
            if (read < 0) throw new IOException("Truncated JPEG marker");
            if (read == 0) continue;
            out.write(chunk, 0, read);
            n -= read;
        }
    }
    private static void skip(InputStream in, long n) throws IOException {
        byte[] chunk = new byte[16 * 1024];
        while (n > 0) {
            int read = in.read(chunk, 0, (int) Math.min(chunk.length, n));
            if (read < 0) throw new IOException("Truncated JPEG marker");
            if (read == 0) continue;
            n -= read;
        }
    }
    private static void copyRemaining(InputStream in, OutputStream out)
            throws IOException {
        byte[] chunk = new byte[32 * 1024];
        int n;
        while ((n = in.read(chunk)) != -1) if (n > 0) out.write(chunk, 0, n);
    }

    static void removeMetadata(InputStream in, OutputStream out) throws IOException {
        if (required(in) != 0xff || required(in) != 0xd8)
            throw new IOException("Not a JPEG");
        out.write(0xff);
        out.write(0xd8);
        // Before SOS every JPEG segment has a size, except standalone markers.
        for (int count = 0; count < 512; count++) {
            if (required(in) != 0xff) throw new IOException("Malformed JPEG segment");
            int marker = required(in);
            while (marker == 0xff) marker = required(in);
            if (marker == 0xd9) throw new IOException("JPEG without scan data");
            if (marker == 0x00 || marker == 0xd8 || (marker >= 0xd0 && marker <= 0xd7))
                throw new IOException("Unexpected JPEG marker");
            int length = (required(in) << 8) | required(in);
            if (length < 2) throw new IOException("Invalid JPEG marker length");
            int payload = length - 2;
            if (marker == 0xda) {
                out.write(0xff);
                out.write(marker);
                out.write(length >>> 8);
                out.write(length & 0xff);
                copy(in, out, payload);
                copyRemaining(in, out);
                return;
            }
            // APP0 JFIF has no photo location; APP2 ICC color profile may be
            // needed for fidelity. Drop every other metadata/application
            // segment and all JPEG comments (EXIF, XMP, GPS, Photoshop).
            boolean metadata = marker == 0xfe
                    || marker >= 0xe1 && marker <= 0xef && marker != 0xe2;
            if (marker == 0xe2) {
                byte[] bytes = new byte[payload];
                int offset = 0;
                while (offset < payload) {
                    int n = in.read(bytes, offset, payload - offset);
                    if (n < 0) throw new IOException("Truncated ICC segment");
                    offset += n;
                }
                byte[] signature = {'I', 'C', 'C', '_', 'P', 'R', 'O', 'F', 'I', 'L', 'E', 0};
                boolean icc = bytes.length >= signature.length;
                for (int i = 0; icc && i < signature.length; i++) {
                    icc = bytes[i] == signature[i];
                }
                if (icc) {
                    out.write(0xff); out.write(marker);
                    out.write(length >>> 8); out.write(length & 0xff);
                    out.write(bytes);
                }
                continue;
            }
            if (metadata) { skip(in, payload); continue; }
            out.write(0xff);
            out.write(marker);
            out.write(length >>> 8);
            out.write(length & 0xff);
            copy(in, out, payload);
        }
        throw new IOException("Excessive JPEG metadata segments");
    }
}
