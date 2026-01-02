from telegram.ext import Updater, CommandHandler
from datetime import datetime

TOKEN = "8392387605:AAFtLyzrDK6Z7XUCpv6QYaIm5Mt5XXdPydQ"

def start(update, context):
    update.message.reply_text(
        "بوت تسجيل غيابات المدرسة الحسنية\n\n"
        "الاستخدام:\n"
        "/غياب اسم_الطالب"
    )

def غياب(update, context):
    if not context.args:
        update.message.reply_text("❗ اكتب اسم الطالب بعد الأمر")
        return

    name = " ".join(context.args)
    date = datetime.now().strftime("%Y-%m-%d %H:%M")

    with open("absences.txt", "a", encoding="utf-8") as f:
        f.write(f"{name} | {date}\n")

    update.message.reply_text(f"✅ تم تسجيل غياب الطالب:\n{name}")

updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("غياب", غياب))

print("Bot started")
updater.start_polling()
updater.idle()