# Android 12 launch logo regression — cold start

Source of regression: Telegram 13.2.2 still declares
`Theme.TMessages.Start` in
`TMessagesProj/src/main/res/values-v31/styles.xml`, using
`android:windowSplashScreenAnimatedIcon=@drawable/tg_splash_320`.
That icon is the Telegram **blue circle with paper plane** seen at
about 120.5 seconds of the user's 2026-11-13 test recording, after
returning to the home screen and opening NabdhGram again. The existing
app-level `nabdhgram_splash.xml` alone was insufficient to ensure
the native module style used by LaunchActivity was branded.

The approved launcher foreground is now installed into both the app
and native Telegram module resources and **both** Android 12 startup
style locations refer to it. The launch background matches the
existing NabdhGram `#04252A` brand. The PNG's transparent
Android-safe-center asset comes from the existing approved
`branding/approved/AppIcon.png`; no new design or Telegram logo.
Android 11 and earlier retain their original safe launch behavior.
The icon picker activity aliases are independent of this OS splash.

Pre-Gradle regression checks verify the actual generated native
Android 12 styles, approved image bytes/transparent corners and
the LaunchActivity manifest theme; Foundation validates that the
source overlay still patches the official Telegram splash.

**Device acceptance:** on an Android 12+ phone, install the test APK
over the existing NabdhGram package, force stop, reopen using the
launcher, switch between at least two icons then cold-launch again,
and verify the system splash displays NabdhGram's logo on the dark
brand background, never Telegram's official plane. Repeat after a
process restart and on light/dark system appearance. A cached
Android launcher/splash animation might persist until launcher
cache refresh; do not claim visual success without on-device proof.

Keep draft upgrade PR #63 unmerged into main pending all current
Arabic text, bubble, login and launcher/splash device QA.
