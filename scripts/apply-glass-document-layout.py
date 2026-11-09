#!/usr/bin/env python3
"""Keep document names and metadata apart when a custom font has taller glyph metrics."""
from pathlib import Path
import sys
if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-document-layout.py TELEGRAM_SOURCE")
p = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/Cells/ChatMessageCell.java"
s = p.read_text(encoding="utf-8")
old = """                titleY = (int) buttonY + dp(4);
                subtitleY = (int) buttonY + dp(27);
                if (docTitleLayout != null && docTitleLayout.getLineCount() > 1) {
                    subtitleY += (docTitleLayout.getLineCount() - 1) * dp(16) + dp(2);
                }"""
new = """                titleY = (int) buttonY + dp(4);
                // Document fonts have variable line height; the upstream fixed
                // 23dp separation can put file size directly over the filename.
                subtitleY = (int) buttonY + dp(27);
                if (documentAttachType == DOCUMENT_ATTACH_TYPE_DOCUMENT && docTitleLayout != null) {
                    subtitleY = titleY + Math.max(dp(23), docTitleLayout.getHeight() + dp(7));
                } else if (docTitleLayout != null && docTitleLayout.getLineCount() > 1) {
                    subtitleY += (docTitleLayout.getLineCount() - 1) * dp(16) + dp(2);
                }"""
if s.count(old) != 1:
    raise SystemExit("Document title/subtitle anchor changed")
s = s.replace(old, new, 1)
old = """                        if (docTitleLayout != null && docTitleLayout.getLineCount() > 1) {
                            photoHeight += (docTitleLayout.getLineCount() - 1) * dp(16);
                        }"""
new = """                        if (docTitleLayout != null) {
                            // Allow room for actual rendered title lines and
                            // metadata; preserve the original minimum height.
                            photoHeight = Math.max(photoHeight, docTitleLayout.getHeight() + dp(32));
                        }"""
if s.count(old) != 1:
    raise SystemExit("Document bubble height anchor changed")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("Glass document metadata now uses measured font heights.")
