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
anchor = """        canvas.drawPath(path, p);
        if (gradientShader != null && isSelected && paintToUse == null) {"""
replacement = """        canvas.drawPath(path, p);
        // NabdhGram Glass: outline only gradient text bubbles using the
        // existing Telegram shape, preserving grouping and tail geometry.
        if (paintToUse == null && gradientShader != null
                && currentType == TYPE_TEXT && !themePreview && !isSelected) {
            Paint nabdhBubbleEdge = new Paint(Paint.ANTI_ALIAS_FLAG);
            nabdhBubbleEdge.setStyle(Paint.Style.STROKE);
            nabdhBubbleEdge.setStrokeWidth(dp(1));
            nabdhBubbleEdge.setColor(isOut ? 0x66FFFFFF : 0x4483B5B5);
            nabdhBubbleEdge.setAlpha((int) (android.graphics.Color.alpha(nabdhBubbleEdge.getColor()) * alpha / 255f));
            canvas.drawPath(path, nabdhBubbleEdge);
        }
        if (gradientShader != null && isSelected && paintToUse == null) {"""
if s.count(anchor) != 1:
    raise SystemExit("MessageDrawable gradient draw anchor changed")
p.write_text(s.replace(anchor, replacement, 1), encoding="utf-8")
print("Glass gradient text bubble outline applied.")
