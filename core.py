import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
    CallbackQueryHandler
)

# =========================
# ENV
# =========================

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS = {
    int(admin_id)
    for admin_id in os.getenv("ADMIN_IDS", "").split(",")
    if admin_id.strip()
}

INVITE_LINK = os.getenv("INVITE_LINK")

MAIN_ADMIN_ID = list(ADMIN_IDS)[0]

# =========================
# STATES
# =========================

AGE, LOCATION, EXPERIENCE, RULES_AGREEMENT, JOIN_REASON = range(5)

# =========================
# DB
# =========================

def get_db_connection():
    return sqlite3.connect('surveys.db')

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(surveys)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'status' not in columns:
            cursor.execute('ALTER TABLE surveys ADD COLUMN status TEXT DEFAULT "NEW"')
        if 'timestamp' not in columns:
            cursor.execute('ALTER TABLE surveys ADD COLUMN timestamp TEXT DEFAULT ""')

        conn.commit()

def is_login_in_db(login):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM surveys WHERE login = ?', (login,))
        return cursor.fetchone() is not None

def get_application_status(login):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM surveys WHERE login = ?', (login,))
        result = cursor.fetchone()
        return result[0] if result else None

def is_application_rejected(login):
    return get_application_status(login) == 'REJECTED'

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_login = update.message.from_user.username or "Unknown"

    if is_login_in_db(user_login):
        status = get_application_status(user_login)
        if status == 'REJECTED':
            await update.message.reply_text('Ваша заявка была отклонена. Повторная подача невозможна.')
        else:
            await update.message.reply_text('Анкета уже заполнена.')
        return ConversationHandler.END

    keyboard = [["Заполнить анкету", "Хочу прочесть FAQ"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        'Привет! Здесь можно заполнить анкету для вступления.',
        reply_markup=reply_markup
    )

# =========================
# FAQ
# =========================

async def faq_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>FAQ Потрясной Курилки</b>\n\n"
        "Мы рады новым участникам.\n\n"
        "Бан без предупреждений.\n"
        "Есть боты для модерации и анализа сообщений.\n"
    )

    keyboard = [["Заполнить анкету", "Хочу прочесть FAQ"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")

# =========================
# FORM FLOW
# =========================

async def fill_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_login = update.message.from_user.username or "Unknown"

    if is_login_in_db(user_login):
        await update.message.reply_text('Анкета уже заполнена.')
        return ConversationHandler.END

    await update.message.reply_text('Введи возраст:', reply_markup=ReplyKeyboardRemove())
    return AGE

async def age_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['age'] = update.message.text
    await update.message.reply_text('Откуда ты?')
    return LOCATION

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['location'] = update.message.text
    await update.message.reply_text('Опыт участия?')
    return EXPERIENCE

async def experience_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['experience'] = update.message.text
    await update.message.reply_text('Готов соблюдать правила?')
    return RULES_AGREEMENT

async def rules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['rules'] = update.message.text
    await update.message.reply_text('Почему хочешь к нам?')
    return JOIN_REASON

# =========================
# SUBMIT
# =========================

async def join_reason_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reason = update.message.text
    user = update.message.from_user
    login = user.username or "Unknown"
    timestamp = datetime.now().isoformat()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO surveys
            (user_id, login, age, location, experience, rules_agreement, join_reason, status, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user.id,
            login,
            context.user_data['age'],
            context.user_data['location'],
            context.user_data['experience'],
            context.user_data['rules'],
            reason,
            "NEW",
            timestamp
        ))
        conn.commit()

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, f"Новая анкета от @{login}")
        except:
            pass

    await context.bot.send_message(
        chat_id=MAIN_ADMIN_ID,
        text=(
            f"НОВАЯ АНКЕТА\n\n"
            f"@{login}\n"
            f"Возраст: {context.user_data['age']}\n"
            f"Откуда: {context.user_data['location']}\n"
            f"Опыт: {context.user_data['experience']}\n"
            f"Причина: {reason}"
        )
    )

    await update.message.reply_text(
        f'Спасибо! Мы ответим в течение 3 часов.\nСсылка: {INVITE_LINK}'
    )

    return ConversationHandler.END

# =========================
# ADMIN CHECK
# =========================

def is_admin(user_id):
    return user_id in ADMIN_IDS

# =========================
# ADMIN PANEL (оставил без изменений логики, только переменные)
# =========================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("Нет доступа.")
        return

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM surveys WHERE status="NEW"')
        new_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM surveys WHERE status="REJECTED"')
        rejected_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM surveys WHERE status="APPROVED"')
        approved_count = cursor.fetchone()[0]

    keyboard = [
        [InlineKeyboardButton(f"NEW ({new_count})", callback_data="folder_NEW")],
        [InlineKeyboardButton(f"REJECTED ({rejected_count})", callback_data="folder_REJECTED")],
        [InlineKeyboardButton(f"APPROVED ({approved_count})", callback_data="folder_APPROVED")],
    ]

    await update.message.reply_text(
        "Админка:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# MAIN
# =========================

def main():
    init_db()

    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Заполнить анкету$"), fill_form)],
        states={
            AGE: [MessageHandler(filters.TEXT, age_handler)],
            LOCATION: [MessageHandler(filters.TEXT, location_handler)],
            EXPERIENCE: [MessageHandler(filters.TEXT, experience_handler)],
            RULES_AGREEMENT: [MessageHandler(filters.TEXT, rules_handler)],
            JOIN_REASON: [MessageHandler(filters.TEXT, join_reason_handler)],
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^Хочу прочесть FAQ$"), faq_handler))
    app.add_handler(conv)
    app.add_handler(CommandHandler("admin", admin))

    app.run_polling()

if __name__ == "__main__":
    main()
