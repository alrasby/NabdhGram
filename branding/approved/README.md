# NabdhGram selected launcher icons (owner-supplied, 2026-11-15)

The owner retained **two** designs from five uploaded references:

- `nabdh-icon-iphone.webp`: from `11.png`, white rounded-square/iPhone glass.
- `nabdh-icon-circular.webp`: from `55.png`, dark circular turquoise ring.

Pixels outside the icons were converted to transparency; the emblem, colors and
aspect ratio remain as in the owner's images. Sources were optimized to 192×192
WebP for Android's maximum normal launcher mipmap resolution; this changes
compression but never re-creates the logo. High-resolution PNG originals and
density-specific versions are in the delivered downloadable ZIP.

Deliberately **excluded from chooser**: Samsung style, the transparent silver
variant and both light/transparent turquoise options. Legacy activity-aliases
remain only to migrate existing installations without stranding users.

The build fails if either source is missing or its SHA-256 differs. The binary
test compares the resulting 192px launcher PNG pixel-for-pixel with decoded
user-source WebP. The app startup splash uses the previously approved
transparent master artwork and is not replaced.
