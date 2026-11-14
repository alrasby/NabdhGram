# إعداد توقيع Release من متصفح GitHub فقط

**لا تحتاج تثبيت Python أو JDK أو GitHub CLI على جهاز Windows.** يستخدم هذا المسار [GitHub Codespaces](https://github.com/codespaces)، مع بيئة افتراضية تشتمل على الأدوات المطلوبة. **لا يجوز حفظ مفتاح التوقيع في المستودع أو رفعه مع commit.**

## 1. فتح البيئة

1. افتح [مستودع NabdhGram](https://github.com/alrasby/NabdhGram).
2. اختر الفرع `release/v1-feature-integration-and-signing`.
3. اضغط **Code → Codespaces → Create codespace on release/v1-feature-integration-and-signing**.
4. ستفتح واجهة تحرير داخل المتصفح. افتح **Terminal → New Terminal**. لا تستخدم PowerShell في `C:\Windows\System32`.

**تحقق من الأدوات داخل Codespaces:**

```bash
python3 --version
keytool -help >/dev/null
gh --version
```

يستخدم الفرع `.devcontainer/devcontainer.json` مع صورة Universal لتجهيز Python وJDK، إضافة إلى ميزة GitHub CLI. إذا فشل تجهيز الصورة، لا تنشئ مفاتيح بديلة في خدمات ويب عشوائية.

## 2. التحقق من صلاحية GitHub Secrets

التوكن الافتراضي داخل Codespaces قد لا يملك صلاحية تغيير **Actions Secrets**. في طرفية Codespaces نفسها فقط:

```bash
unset GITHUB_TOKEN GH_TOKEN
gh auth login --web --scopes repo
gh secret list -R alrasby/NabdhGram --app actions
```

ستظهر خطوة دخول إلى GitHub عبر المتصفح. يجب أن يعمل أمر `gh secret list` قبل إنشاء المفاتيح؛ إذا ظهر خطأ 403، راجع صلاحيات حسابك بدلًا من مشاركة أي token أو كلمة مرور مع الآخرين.

## 3. إنشاء مفتاح ملكك مرة واحدة

إذا لم يسبق لك إصدار نسخة عامة بمفتاح إنتاجي، نفّذ في Codespaces:

```bash
python3 tools/setup-release-secrets.py --create "$HOME/NabdhGramPrivate/nabdhgram-release.jks"
```

أدخل كلمة مرور قوية وحافظ عليها. **لا تُنشئ مفتاحًا جديدًا إذا كان لديك مفتاح Release قديم**؛ استخدم خيار `--existing` للمفتاح القديم بدل `--create` لأن تغييره يقطع قابلية الترقية بالتوقيع نفسه.

يُنشئ الأمر ملفًا خاصًا في مسار خارج المستودع ويرفع خمسة **Actions Secrets** مباشرة إلى GitHub. لا يطبع محتويات المفتاح أو كلمات المرور. عند الانتهاء افتح [إعدادات أسرار Actions في المستودع](https://github.com/alrasby/NabdhGram/settings/secrets/actions) للتحقق من أسماء الأسرار فقط، لا قيمها.

## 4. الاحتفاظ بالمفتاح خارج Codespaces — ضروري جدًا

قبل حذف البيئة السحابية، **نزّل `$HOME/NabdhGramPrivate/nabdhgram-release.jks` إلى حاسوبك**، ثم أنشئ نسخة احتياطية مشفرة خارج الإنترنت واحتفظ بكلمة المرور بأمان. يمكنك إضافة مجلد `/home/codespace/NabdhGramPrivate` إلى مستكشف ملفات VS Code داخل Codespaces عبر **File → Add Folder to Workspace**، ثم النقر بزر الفأرة الأيمن على `nabdhgram-release.jks` واختيار **Download**. إذا لم يتوفر الأمر، استخدم واجهة مدير الملفات في Codespaces لتنزيل الملف، **ولا تنسخه إلى المستودع أو ملفات Git**.

لا تحذف Codespace حتى تتحقق أن الملف نُزّل بالفعل ويصلح للاستخدام، وأن كلمات المرور محفوظة. ثم احذف Codespace من [github.com/codespaces](https://github.com/codespaces) لإزالة النسخة السحابية المؤقتة. لا تلتقط صورًا للشاشة تحتوي على أسرار.

## 5. إعداد Firebase دون تثبيت برامج محليًا

1. افتح [Firebase Console](https://console.firebase.google.com/) وأنشئ مشروع NabdhGram (إن لم يوجد).
2. أضف تطبيق **Android** بمعرف الحزمة **`net.nabdhserv.nabdhgram`** بالضبط.
3. نزّل `google-services.json` على حاسوبك.
4. ارفع الملف داخل Codespaces إلى مساحة مؤقتة خارج المستودع إن أمكن؛ عند الرفع إلى مساحة المشروع لا تنفّذ أي `git add` له، وانقله مباشرة خارج المستودع.
5. أعد فتح Codespace نفسه، وسجّل دخول `gh` إذا لزم، ثم استخدم `--existing` مع ملف المفتاح السابق و`--firebase-json` لمسار الملف، لكي يُضاف السر السادس إلى GitHub دون تدوير مفتاح التوقيع.

مثال فقط بعد وضع الملف **خارج** مجلد المشروع:

```bash
python3 tools/setup-release-secrets.py --existing "$HOME/NabdhGramPrivate/nabdhgram-release.jks" --firebase-json "$HOME/NabdhGramPrivate/google-services.json"
```

**الأسرار الستة في Actions** تشمل مفتاح Android، كلمة مرور المخزن، اسم المفتاح، كلمة مرور المفتاح، بصمة الشهادة، وملف Firebase المشفر بصيغة Base64. وهي مختلفة تمامًا عن Codespaces secrets.

## 6. بناء النسخة الحقيقية

مسار `NabdhGram owner-signed Release APK` يعمل **يدويًا من main فقط** بعد دمج حزمة الإصدار الأول واكتمال الاختبارات. إنشاء الأسرار الآن لا يشغّل Release تلقائيًا.

**تحذير التحديث:** إذا كان التطبيق المثبّت مسبقًا يحمل توقيع Debug مختلفًا، لن تُثبت نسخة Release فوقه مباشرةً. حافظ على بيانات الحساب والملفات المهمة ولا تحذف التطبيق قبل إعداد اختبار انتقال مناسب.

لا تشارك مفاتيح Release أو كلمات مرورها في ChatGPT أو تذاكر GitHub.
