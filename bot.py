import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import json
import os

# ================== الإعدادات ==================
TOKEN = "8392387605:AAHrTsFXXIoyL_6uRbWH_sZi9I9Ef5LGmMk"

TEACHERS_FILE = "teachers.json"
STUDENTS_FILE = "students.json"
AUTH_FILE = "authorized_users.json"

bot = telebot.TeleBot(TOKEN)
user_state = {}
waiting_action = {}

# ================== دوال مساعدة ==================
def load_json(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_authorized(user_id):
    if not os.path.exists(AUTH_FILE):
        return False
    with open(AUTH_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return user_id in data.get("allowed", [])

# ================== /start ==================
@bot.message_handler(commands=['start'])
def start(message):
    if not is_authorized(message.from_user.id):
        bot.reply_to(message, "❌ عذرًا، لا تملك صلاحية استخدام البوت.")
        return

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("➕ تسجيل حضور / غياب", callback_data="start_att"),
    )
    kb.add(
        InlineKeyboardButton("🔐 إدارة الصلاحيات", callback_data="permissions")
    )

    bot.send_message(
        message.chat.id,
        "اختر من القائمة:",
        reply_markup=kb
    )

# ================== أزرار ==================
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    if not is_authorized(call.from_user.id):
        bot.answer_callback_query(call.id, "غير مخوّل", show_alert=True)
        return

    chat_id = call.message.chat.id
    data = call.data

    teachers = load_json(TEACHERS_FILE)
    students = load_json(STUDENTS_FILE)

    # ---- تسجيل حضور ----
    if data == "start_att":
        kb = InlineKeyboardMarkup()
        for t in teachers:
            kb.add(InlineKeyboardButton(t, callback_data=f"teacher|{t}"))
        bot.edit_message_text("اختر الأستاذ:", chat_id, call.message.id, reply_markup=kb)

    elif data.startswith("teacher|"):
        teacher = data.split("|")[1]
        user_state[chat_id] = {"teacher": teacher}
        kb = InlineKeyboardMarkup()
        for s in teachers.get(teacher, []):
            kb.add(InlineKeyboardButton(s, callback_data=f"subject|{s}"))
        bot.edit_message_text("اختر المادة:", chat_id, call.message.id, reply_markup=kb)

    elif data.startswith("subject|"):
        subject = data.split("|")[1]
        user_state[chat_id]["subject"] = subject
        kb = InlineKeyboardMarkup()
        for st in students.get(subject, []):
            kb.add(InlineKeyboardButton(st, callback_data=f"student|{st}"))
        bot.edit_message_text("اختر الطالب:", chat_id, call.message.id, reply_markup=kb)

    elif data.startswith("student|"):
        student = data.split("|")[1]
        user_state[chat_id]["student"] = student
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("✅ حاضر", callback_data="status|present"),
            InlineKeyboardButton("❌ غائب", callback_data="status|absent")
        )
        bot.edit_message_text(
            f"الطالب: {student}\nاختر الحالة:",
            chat_id,
            call.message.id,
            reply_markup=kb
        )

    elif data.startswith("status|"):
        status = "حاضر" if data.endswith("present") else "غائب"
        info = user_state.pop(chat_id)

        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open("attendance.txt", "a", encoding="utf-8") as f:
            f.write(
                f"{info['student']} | {info['teacher']} | {info['subject']} | {status} | {date}\n"
            )

        bot.edit_message_text(
            f"✅ تم التسجيل\n\n"
            f"الطالب: {info['student']}\n"
            f"المادة: {info['subject']}\n"
            f"الحالة: {status}",
            chat_id,
            call.message.id
        )

    # ---- إدارة الصلاحيات ----
    elif data == "permissions":
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("➕ إضافة مخوّل", callback_data="add_auth"),
            InlineKeyboardButton("➖ حذف مخوّل", callback_data="remove_auth")
        )
        bot.edit_message_text(
            "لوحة إدارة الصلاحيات:",
            chat_id,
            call.message.id,
            reply_markup=kb
        )

    elif data == "add_auth":
        bot.send_message(chat_id, "✏️ أرسل Telegram ID للإضافة")
        waiting_action[chat_id] = "add"

    elif data == "remove_auth":
        bot.send_message(chat_id, "✏️ أرسل Telegram ID للحذف")
        waiting_action[chat_id] = "remove"

# ================== إضافة / حذف مخوّل ==================
@bot.message_handler(func=lambda m: m.chat.id in waiting_action)
def handle_auth_change(message):
    if not is_authorized(message.from_user.id):
        return

    try:
        user_id = int(message.text.strip())
    except:
        bot.reply_to(message, "❗ أرسل رقم ID فقط")
        return

    data = load_json(AUTH_FILE)
    if "allowed" not in data:
        data["allowed"] = []

    if waiting_action[message.chat.id] == "add":
        if user_id not in data["allowed"]:
            data["allowed"].append(user_id)
            bot.reply_to(message, "✅ تم إضافة المخوّل")
        else:
            bot.reply_to(message, "ℹ️ المستخدم موجود مسبقًا")

    elif waiting_action[message.chat.id] == "remove":
        if user_id in data["allowed"]:
            data["allowed"].remove(user_id)
            bot.reply_to(message, "🗑️ تم حذف المخوّل")
        else:
            bot.reply_to(message, "ℹ️اسم المستخدم غير موجود")

    save_json(AUTH_FILE, data)
    del waiting_action[message.chat.id]

# ================== تشغيل البوت ==================
print("Bot started")
bot.infinity_polling(timeout=10, long_polling_timeout=5)