#!/usr/bin/env python3
"""Use the native Telegram bubble geometry for theme-aware text and media edges.

This leaves selection, theme previews, media content and message grouping intact.
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
        // NabdhGram Glass: outline gradient text and media bubbles using the
        // existing Telegram shape, preserving grouping and tail geometry.
        if (paintToUse == null && gradientShader != null
                && (currentType == TYPE_TEXT || currentType == TYPE_MEDIA) && !themePreview && !isSelected) {
            nabdhBubbleEdge.setStyle(Paint.Style.STROKE);
            nabdhBubbleEdge.setStrokeWidth(dp(1.1f));
            // The native shadow can be transparent in .attheme presets.
            // Fall back to the message-panel text hue without hardcoding
            // mint, black or white; otherwise Glass is effectively invisible.
            int nabdhEdgeColor = getColor(isOut
                    ? Theme.key_chat_outBubbleShadow : Theme.key_chat_inBubbleShadow);
            if (Color.alpha(nabdhEdgeColor) < 35) {
                nabdhEdgeColor = getColor(Theme.key_chat_messagePanelText);
            }
            nabdhBubbleEdge.setColor(Color.rgb(Color.red(nabdhEdgeColor),
                    Color.green(nabdhEdgeColor), Color.blue(nabdhEdgeColor)));
            nabdhBubbleEdge.setAlpha((int) (90f * alpha / 255f));
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
                if ((currentType == TYPE_TEXT || currentType == TYPE_MEDIA) && !themePreview && !isSelected) {
                    int stroke = getColor(isOut
                            ? Theme.key_chat_outBubbleShadow : Theme.key_chat_inBubbleShadow);
                    if (Color.alpha(stroke) < 30) {
                        stroke = getColor(Theme.key_chat_messagePanelText);
                    }
                    nabdhBubbleEdge.setStyle(Paint.Style.STROKE);
                    nabdhBubbleEdge.setStrokeWidth(dp(0.8f));
                    nabdhBubbleEdge.setColor(Color.rgb(Color.red(stroke),
                            Color.green(stroke), Color.blue(stroke)));
                    nabdhBubbleEdge.setAlpha((int) (53f * alpha / 255f));
                    canvas.drawPath(makePath(), nabdhBubbleEdge);
                }
                return;"""
s = s.replace(cached, cached_stroke, 1)
p.write_text(s, encoding="utf-8")
print("Glass text/media bubble outlines applied using native Telegram paths.")
