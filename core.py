import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
    CallbackQueryHandler
)
from telegram.error import TimedOut, BadRequest
from datetime import datetime

TOKEN = "7828229702:AAGu34KJ_-GZCXSMSf26ASMNaocjSbnMU7M"
ADMIN_IDS = {5146489793, 5926211085}
AGE, LOCATION, EXPERIENCE, RULES_AGREEMENT, JOIN_REASON = range(5)


def is_admin(user_id):
    return user_id in ADMIN_IDS

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
        cursor.execute('SELECT status FROM surveys WHERE login = ?', (login,))
        result = cursor.fetchone()
        return result is not None and result[0] != 'REJECTED'

def is_application_rejected(login):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM surveys WHERE login = ?', (login,))
        result = cursor.fetchone()
        return result and result[0] == 'REJECTED'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_login = update.message.from_user.username or "Unknown"

    keyboard = [["Заполнить анкету"], ["Хочу прочесть FAQ"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
    await update.message.reply_text(
        'Привет! Спасибо за интерес к нашей конференции. Здесь можно заполнить анкету для вступления или прочитать FAQ.',
        reply_markup=reply_markup
    )

async def faq_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "<b>Мы - конференция AURA и мы будем рады новым людям.</b>\n\n"
        "<u><b>FAQ по чату:</b></u>\n\n"
        "<b>- Есть ли здесь место для меня?</b>\n"
        "Мы рады новым участникам, которые разделяют наши интересы и готовы общаться на равных. "
        "Если вы пришли просто за вниманием или ищете новых знакомств ради развлечений, то это не наш чат.\n\n"
        "<b>- Есть ли система предупреждений?</b>\n"
        "Нет, мы сразу принимаем решения о бане.\n\n"
        "<b>- Какие у вас есть боты?</b>\n"
        "У нас есть бот Chat Norris, который делает саммари последних 400 сообщений, имеет встроенный GPT и функцию "
        "«прожарки» постов. Также есть Iris, который приветствует новеньких и помогает банить. И есть Курилкабот, "
        "который я создаю и тестирую сам. Ну и этот бот, в котором вы сейчас читаете этот текст.\n\n"
        "<b>- А расшифровщик голосовых есть?</b>\n"
        "В группе достаточно голосов, расшифровка голосовых сообщений доступна всем участникам, "
        "в том числе и без подписки Премиум в ТГ.\n\n"
        "<b>- Откуда вы взялись и чем живете?</b>\n"
        "Мы появились в ВК около 8 лет назад. Изначально это была ролевая конфа с множеством участников, "
        "но со временем мы убрали фейков и фриков, вектор развития переместился на реал и чат стал более дружелюбным. "
        "В 2021 году мы переехали в ТГ. За все время у нас сменилось около тысячи человек. Мы стали встречаться в реале, "
        "дарить подарки на дни рождения и поняли, что мы не просто чувачки в интернете, а настоящие друзья. "
        "И стараемся пополнять этот список друзей.",
        parse_mode="HTML"
    )


# ... остальной код анкеты остаётся без изменений ...

async def safe_edit_message_text(message, text, reply_markup=None):
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TimedOut:
        print("Timeout while editing message")
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise

# Функция для уведомления всех админов о новой анкете
async def notify_admins_about_application(context: ContextTypes.DEFAULT_TYPE, user_login: str):
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=f"Новая анкета от @{user_login}!")
        except Exception as e:
            print(f"Не удалось отправить сообщение админу {admin_id}: {e}")

# В main добавим обработчик faq
application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^Хочу прочесть FAQ$'), faq_handler))
