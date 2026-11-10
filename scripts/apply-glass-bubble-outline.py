#!/usr/bin/env python3
"""Add a subtle border to gradient text bubbles using Telegram's own bubble path.

Solid-color bubbles retain the upstream cached drawable; media, previews,
selection overlays and custom theme preview drawing are left unchanged.
"""
from pathlib import Path
import sys
if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-bubble-outline.py TELEGRAM_SOURCE")
p = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/ActionBar/MessageDrawable.java"
s = p.read_text(encoding="utf-8")
field_anchor = "    private int currentBackgroundHeight;\n"
if s.count(field_anchor) != 1:
    raise SystemExit("MessageDrawable field anchor changed")
s = s.replace(field_anchor, field_anchor + "    private final Paint nabdhBubbleEdge = new Paint(Paint.ANTI_ALIAS_FLAG);" + chr(10), 1)
anchor = """        canvas.drawPath(path, p);
        if (gradientShader != null && isSelected && paintToUse == null) {"""
replacement = """        canvas.drawPath(path, p);
        // NabdhGram Glass: outline only gradient text bubbles using the
        // existing Telegram shape, preserving grouping and tail geometry.
        if (paintToUse == null && gradientShader != null
                && currentType == TYPE_TEXT && !themePreview && !isSelected) {
            nabdhBubbleEdge.setStyle(Paint.Style.STROKE);
            nabdhBubbleEdge.setStrokeWidth(dp(1));
            // Respect the active theme's in/out shadow hue, including user
            // imported .attheme files. Avoid fixed turquoise or white.
            nabdhBubbleEdge.setColor(Theme.getColor(isOut
                    ? Theme.key_chat_outBubbleShadow : Theme.key_chat_inBubbleShadow));
            nabdhBubbleEdge.setAlpha((int) (android.graphics.Color.alpha(nabdhBubbleEdge.getColor()) * alpha / 255f));
            canvas.drawPath(path, nabdhBubbleEdge);
        }
        if (gradientShader != null && isSelected && paintToUse == null) {"""
if s.count(anchor) != 1:
    raise SystemExit("MessageDrawable gradient draw anchor changed")
s = s.replace(anchor, replacement, 1)
# The upstream renderer returns early for ordinary solid-color text bubbles.
# Without this branch, only gradient bubbles ever show a Glass outline.
cached = """                background.setBounds(bounds);
                background.draw(canvas);
                return;"""
if s.count(cached) != 1:
    raise SystemExit("Cached Telegram bubble drawing branch changed")
cached_stroke = """                background.setBounds(bounds);
                background.draw(canvas);
                if (currentType == TYPE_TEXT && !themePreview && !isSelected) {
                    int stroke = getColor(isOut
                            ? Theme.key_chat_outBubbleShadow : Theme.key_chat_inBubbleShadow);
                    if (Color.alpha(stroke) < 30) {
                        stroke = getColor(Theme.key_chat_messagePanelText);
                    }
                    nabdhBubbleEdge.setStyle(Paint.Style.STROKE);
                    nabdhBubbleEdge.setStrokeWidth(dp(0.8f));
                    nabdhBubbleEdge.setColor(stroke);
                    nabdhBubbleEdge.setAlpha((int) (53f * alpha / 255f));
                    canvas.drawPath(makePath(), nabdhBubbleEdge);
                }
                return;"""
s = s.replace(cached, cached_stroke, 1)
p.write_text(s, encoding="utf-8")
print("Glass gradient text bubble outline applied.")
