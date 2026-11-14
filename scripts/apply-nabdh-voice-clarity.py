#!/usr/bin/env python3
"""Opt-in modest voice-only gain on the native ExoPlayer audio session.

This is *not* noise cancellation or speech enhancement DSP. The gain effect
is optional, bounded and fails safely when an OEM disables audio effects.
No changes to voice calls, video, music, Telegram transport or recording.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-voice-clarity.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve()
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
media = root / "TMessagesProj/src/main/java/org/telegram/messenger/MediaController.java"
player = ui / "Components/VideoPlayer.java"
settings = ui / "NabdhGramFeatureCategoryActivity.java"

def once(path, old, new, label):
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Voice Clarity {label}: expected one anchor; got {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")

# This is the existing, user-selected message audio player, not the voice
# calling pipeline. Set before prepare so the Player.Listener session callback
# can attach to the actual Android audio session after ExoPlayer allocates it.
once(media, "                audioPlayer = new VideoPlayer();",
    """                audioPlayer = new VideoPlayer();
                audioPlayer.nabdhEnableVoiceBoost(messageObject.isVoice()
                        && ApplicationLoader.applicationContext.getSharedPreferences(
                            "nabdhgram_audio", Context.MODE_PRIVATE)
                            .getBoolean("voice_boost_enabled", false));""",
    "voice-only player routing")

once(player, "    private ExoPlayer audioPlayer;",
    """    private ExoPlayer audioPlayer;

    // Optional gain is per voice-message playback session; it never alters
    // source audio or audio played through calls, video or music.
    private boolean nabdhVoiceBoostRequested;
    private int nabdhVoiceSessionId;
    private android.media.audiofx.LoudnessEnhancer nabdhVoiceBoost;

    public void nabdhEnableVoiceBoost(boolean enabled) {
        nabdhVoiceBoostRequested = enabled;
        if (!enabled) nabdhReleaseVoiceBoost();
    }

    private void nabdhReleaseVoiceBoost() {
        if (nabdhVoiceBoost != null) {
            try {
                nabdhVoiceBoost.setEnabled(false);
                nabdhVoiceBoost.release();
            } catch (RuntimeException ignored) {
                // Some OEM audio effects fail while a session is shutting down.
            } finally {
                nabdhVoiceBoost = null;
                nabdhVoiceSessionId = 0;
            }
        }
    }

    @Override
    public void onAudioSessionIdChanged(int audioSessionId) {
        if (!nabdhVoiceBoostRequested || audioSessionId <= 0) return;
        if (audioSessionId == nabdhVoiceSessionId && nabdhVoiceBoost != null) return;
        nabdhReleaseVoiceBoost();
        android.media.audiofx.LoudnessEnhancer effect = null;
        try {
            effect = new android.media.audiofx.LoudnessEnhancer(audioSessionId);
            // Modest 2.5 dB gain; no aggressive compression or clipping claims.
            effect.setTargetGain(250);
            effect.setEnabled(true);
            nabdhVoiceBoost = effect;
            nabdhVoiceSessionId = audioSessionId;
        } catch (RuntimeException unsupportedEffect) {
            if (effect != null) {
                try { effect.release(); } catch (RuntimeException ignored) { }
            }
            // Fall back to ordinary Telegram voice playback without crashing.
            nabdhVoiceBoost = null;
            nabdhVoiceSessionId = 0;
        }
    }
""", "per-session audio effect")

once(player, "    public void releasePlayer(boolean async) {\n        activePlayers.remove(playerId);",
    """    public void releasePlayer(boolean async) {
        nabdhReleaseVoiceBoost();
        activePlayers.remove(playerId);""", "release audio effect")

once(settings, "        fragmentView = scroll;",
    """        if (featureId == 402) {
            addNabdhVoiceBoost(context, content);
        }
        fragmentView = scroll;""", "voice settings route")
once(settings, "    private void addPrivacyControls(Context context, LinearLayout content) {",
    """    private void addNabdhVoiceBoost(Context context, LinearLayout content) {
        LinearLayout card = new LinearLayout(context);
        card.setOrientation(LinearLayout.VERTICAL);
        int padding = nabdhDp(context, 16);
        card.setPadding(padding, padding, padding, padding);
        card.setBackground(org.telegram.ui.Components.NabdhGlassRowDecoration.newCardBackground());
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, -2);
        lp.topMargin = nabdhDp(context, 12);
        content.addView(card, lp);
        android.content.SharedPreferences prefs = context.getSharedPreferences(
                "nabdhgram_audio", Context.MODE_PRIVATE);
        android.widget.Switch gentleBoost = new android.widget.Switch(context);
        gentleBoost.setText(nabdhText(context, R.string.NabdhVoiceBoostLabel));
        gentleBoost.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        gentleBoost.setChecked(prefs.getBoolean("voice_boost_enabled", false));
        gentleBoost.setOnCheckedChangeListener((button, checked) ->
                prefs.edit().putBoolean("voice_boost_enabled", checked).apply());
        card.addView(gentleBoost);
        TextView note = new TextView(context);
        note.setText(nabdhText(context, R.string.NabdhVoiceBoostNote));
        note.setTextSize(13);
        note.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
        card.addView(note);
    }

    private void addPrivacyControls(Context context, LinearLayout content) {""",
    "voice Glass detail")

values = {
    "values": {
        "NabdhVoiceBoostLabel": "Gentle voice-message boost",
        "NabdhVoiceBoostNote": "Optional 2.5 dB playback gain for voice messages only, from the next message. This does not remove noise or change calls, music, videos or recordings. Audio-effect availability depends on your device. May increase perceived loudness."
    },
    "values-ar": {
        "NabdhVoiceBoostLabel": "تعزيز خفيف لصوت الرسائل",
        "NabdhVoiceBoostNote": "رفع اختياري محدود للصوت بمقدار 2.5 ديسيبل للرسائل الصوتية فقط، بدءًا من الرسالة التالية. لا يزيل الضوضاء ولا يغيّر المكالمات أو الموسيقى أو الفيديو أو التسجيلات. قد لا يدعم الجهاز التأثير، وقد يرتفع مستوى الصوت المسموع."
    }
}
for locale, strings in values.items():
    target = root / "TMessagesProj/src/main/res" / locale / "nabdh_voice_boost.xml"
    if target.exists():
        raise SystemExit("Duplicate Voice Clarity translation: " + locale)
    rows = ['<?xml version="1.0" encoding="utf-8"?>', '<resources>']
    for name, value in strings.items():
        rows.append('    <string name="' + name + '">' + escape(value).replace("'", "\\'") + '</string>')
    rows.append('</resources>')
    target.write_text("\n".join(rows) + "\n", encoding="utf-8")
print("PASS: opt-in native voice playback gain, session lifecycle and localized Glass control")
