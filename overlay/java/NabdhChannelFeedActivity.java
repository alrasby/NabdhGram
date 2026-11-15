package org.telegram.ui;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.telegram.messenger.ChatObject;
import org.telegram.messenger.MessageObject;
import org.telegram.messenger.MessagesController;
import org.telegram.messenger.UserConfig;
import org.telegram.tgnet.TLRPC;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Read-only, on-demand latest cached post per joined broadcast channel.
 * A refresh never requests or marks messages read. No chat content is stored.
 */
public final class NabdhChannelFeedActivity extends Activity {
    private LinearLayout items;
    private String local(String en, String ar) {
        return org.telegram.messenger.LocaleController.isRTL ? ar : en;
    }
    private final int account = UserConfig.selectedAccount;
    private static final class Post {
        final long dialog;
        final String title;
        final String username;
        final int messageId, date;
        final String preview;
        Post(long dialog, String title, String username,
             int messageId, int date, String preview) {
            this.dialog = dialog;
            this.title = title;
            this.username = username;
            this.messageId = messageId;
            this.date = date;
            this.preview = preview;
        }
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        setTitle(local("Channel Feed", "موجز القنوات"));
        LinearLayout screen = new LinearLayout(this);
        screen.setOrientation(LinearLayout.VERTICAL);
        screen.setLayoutDirection(org.telegram.messenger.LocaleController.isRTL
                ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        int pad = (int) (12 * getResources().getDisplayMetrics().density);
        screen.setPadding(pad, pad, pad, pad);
        screen.setBackgroundColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhite));
        TextView note = new TextView(this);
        note.setText(local("Latest locally cached post from your channels · Read-only · No background scanning",
                "أحدث منشور محفوظ محليًا من قنواتك · للقراءة فقط · دون فحص في الخلفية"));
        note.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteGrayText2));
        note.setTextSize(13);
        note.setPadding(6, 4, 6, 12);
        screen.addView(note);
        Button reload = new Button(this);
        reload.setText(local("Refresh channel posts", "تحديث منشورات القنوات"));
        reload.setAllCaps(false);
        reload.setOnClickListener(v -> render());
        screen.addView(reload);
        ScrollView scroll = new ScrollView(this);
        items = new LinearLayout(this);
        items.setOrientation(LinearLayout.VERTICAL);
        scroll.addView(items);
        screen.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1f));
        org.telegram.ui.Components.NabdhToolUi.install(this, screen,
                local("Channel Feed", "موجز القنوات"));
        render();
    }

    @Override protected void onResume() {
        super.onResume();
        // Refresh after a PIN-lock change in another screen; do not reuse
        // already rendered cached post text from a newly protected channel.
        if (items != null) render();
    }

    private List<Post> cachedPosts() {
        ArrayList<Post> posts = new ArrayList<>();
        MessagesController controller = MessagesController.getInstance(account);
        if (controller == null || controller.dialogs_dict == null) return posts;
        for (int i = 0; i < controller.dialogs_dict.size(); i++) {
            TLRPC.Dialog dialog = controller.dialogs_dict.valueAt(i);
            if (dialog == null || dialog.id >= 0) continue;
            // An opt-in locked channel must not leak cached post text through
            // this independent feed, even when its ChatActivity PIN gate works.
            if (org.telegram.ui.Components.NabdhChatLock.isLocked(
                    getApplicationContext(), account, dialog.id)) continue;
            TLRPC.Chat chat = controller.getChat(-dialog.id);
            if (chat == null || !ChatObject.isChannel(chat) || chat.megagroup) continue;
            ArrayList<MessageObject> messages = controller.dialogMessage.get(dialog.id);
            if (messages == null || messages.isEmpty()) continue;
            MessageObject latest = messages.get(0);
            if (latest == null || latest.messageOwner == null) continue;
            String body = latest.messageText == null ? "" : latest.messageText.toString();
            if (body.length() > 360) body = body.substring(0, 360) + "…";
            if (body.trim().isEmpty()) body = local("[Media post]", "[منشور وسائط]");
            posts.add(new Post(dialog.id, chat.title,
                    chat.username, latest.messageOwner.id,
                    latest.messageOwner.date, body));
        }
        Collections.sort(posts, (left, right) -> Integer.compare(right.date, left.date));
        return posts;
    }

    private void openChannel(Post post) {
        Intent intent = new Intent(this, LaunchActivity.class);
        intent.putExtra("chatId", -post.dialog);
        intent.putExtra("currentAccount", account);
        intent.setAction("com.tmessages.openchat" + System.nanoTime());
        startActivity(intent);
    }

    private void copyPublicLink(Post post) {
        if (post.username == null || post.username.isEmpty() || post.messageId <= 0) {
            Toast.makeText(this, local("Private channel has no public post link", "هذه القناة خاصة ولا يتوفر رابط عام للمنشور"), Toast.LENGTH_SHORT).show();
            return;
        }
        String url = "https://t.me/" + post.username + "/" + post.messageId;
        ClipboardManager clip = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        if (clip != null) clip.setPrimaryClip(ClipData.newPlainText("Channel post", url));
        Toast.makeText(this, local("Post link copied", "تم نسخ رابط المنشور"), Toast.LENGTH_SHORT).show();
    }

    private void render() {
        items.removeAllViews();
        List<Post> posts = cachedPosts();
        if (posts.isEmpty()) {
            TextView empty = new TextView(this);
            empty.setText(local("No cached channel posts yet. Open your channels in Telegram, then refresh.",
                    "لا توجد منشورات محفوظة حاليًا. افتح قنواتك في Telegram ثم حدّث الموجز."));
            empty.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                    org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteGrayText2));
            items.addView(empty);
            return;
        }
        int p = (int) (16 * getResources().getDisplayMetrics().density);
        for (Post post : posts) {
            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.VERTICAL);
            card.setPadding(p, p, p, p);
            card.setBackground(
                    org.telegram.ui.Components.NabdhGlassRowDecoration.newCardBackground());
            TextView title = new TextView(this);
            title.setText(post.title);
            title.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                    org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteBlackText));
            title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
            title.setTextSize(17);
            card.addView(title);
            TextView date = new TextView(this);
            date.setText(android.text.format.DateFormat.format("yyyy-MM-dd HH:mm",
                    post.date * 1000L));
            date.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                    org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteGrayText2));
            card.addView(date);
            TextView content = new TextView(this);
            content.setText(post.preview);
            content.setTextSize(15);
            content.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                    org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteBlackText));
            content.setPadding(0, p / 2, 0, p / 2);
            card.addView(content);
            TextView hint = new TextView(this);
            hint.setText(local("Tap: open channel · Swipe left: copy public link",
                    "اضغط لفتح القناة · اسحب لليسار لنسخ رابط المنشور"));
            hint.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                    org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteGrayText2));
            hint.setTextSize(11);
            card.addView(hint);
            card.setOnClickListener(v -> openChannel(post));
            card.setOnTouchListener(new View.OnTouchListener() {
                float startX, startY;
                @Override public boolean onTouch(View v, MotionEvent event) {
                    if (event.getActionMasked() == MotionEvent.ACTION_DOWN) {
                        startX = event.getX();
                        startY = event.getY();
                        return true;
                    }
                    if (event.getActionMasked() == MotionEvent.ACTION_UP) {
                        float x = event.getX() - startX;
                        float y = event.getY() - startY;
                        float threshold = 64 * getResources().getDisplayMetrics().density;
                        if (Math.abs(x) > threshold && Math.abs(x) > Math.abs(y) * 1.4f) {
                            if (x < 0) copyPublicLink(post);
                            else openChannel(post);
                        } else if (Math.abs(x) < threshold && Math.abs(y) < threshold) {
                            openChannel(post);
                        }
                        return true;
                    }
                    return true;
                }
            });
            LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
            params.bottomMargin = p / 2;
            items.addView(card, params);
        }
    }
}
