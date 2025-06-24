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
from datetime import datetime

# Токен вашего бота
TOKEN = "7828229702:AAGu34KJ_-GZCXSMSf26ASMNaocjSbnMU7M"

# Идентификаторы администраторов
ADMIN_IDS = {5146489793, 5926211085}

# Состояния для ConversationHandler
AGE, LOCATION, EXPERIENCE, RULES_AGREEMENT, JOIN_REASON = range(5)

# Проверка прав доступа
def is_admin(user_id):
    return user_id in ADMIN_IDS

def get_db_connection():
    return sqlite3.connect('surveys.db')

# Инициализация базы данных
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
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
    await update.message.reply_text(
        'Привет! Спасибо за интерес к нашей конференции. Здесь можно заполнить анкету для вступления, это займет пару минут. Анкеты рассматриваются вручную в течение трех часов.',
        reply_markup=reply_markup
    )

async def faq_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "<b>Мы - конференция AURA и мы будем рады новым людям.</b>\n\n"
        "<u><b>FAQ по чату:</b></u>\n\n"
        "<b>- Есть ли здесь место для меня?</b>\n"
        "Мы рады новым участникам, которые разделяют наши интересы и готовы общаться на равных."
        " Если вы пришли просто за вниманием или ищете новых знакомств ради развлечений, то это не наш чат.\n\n"
        "<b>- Есть ли система предупреждений?</b>\n"
        "Нет, мы сразу принимаем решения о бане.\n\n"
        "<b>- Какие у вас есть боты?</b>\n"
        "У нас есть бот Chat Norris, который делает саммари последних 400 сообщений, имеет встроенный GPT и функцию"
        " «прожарки» постов. Также есть Iris, который приветствует новеньких и помогает банить. И есть Курилкабот,"
        " который я создаю и тестирую сам. Ну и этот бот, в котором вы сейчас читаете этот текст.\n\n"
        "<b>- А расшифровщик голосовых есть?</b>\n"
        "В группе достаточно голосов, расшифровка голосовых сообщений доступна всем участникам,"
        " в том числе и без подписки Премиум в ТГ.\n\n"
        "<b>- Откуда вы взялись и чем живете?</b>\n"
        "Мы появились в ВК около 8 лет назад. Изначально это была ролевая конфа с множеством участников,"
        " но со временем мы убрали фейков и фриков, вектор развития переместился на реал и чат стал более дружелюбным."
        " В 2021 году мы переехали в ТГ. За все время у нас сменилось около тысячи человек. Мы стали встречаться в реале,"
        " дарить подарки на дни рождения и поняли, что мы не просто чувачки в интернете, а настоящие друзья."
        " И стараемся пополнять этот список друзей.",
        parse_mode="HTML"
    )
    keyboard = [["Заполнить анкету", "Хочу прочесть FAQ"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
    await update.message.reply_text(faq_text, reply_markup=reply_markup)

async def fill_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_login = update.message.from_user.username or "Unknown"

    if is_login_in_db(user_login):
        if is_application_rejected(user_login):
            await update.message.reply_text('Ваша заявка была отклонена. Повторная подача невозможна.')
        else:
            await update.message.reply_text('Анкета уже заполнена.')
        return ConversationHandler.END

    await update.message.reply_text('Пожалуйста, введи свой возраст:', reply_markup=ReplyKeyboardRemove())
    return AGE

async def age_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['age'] = update.message.text[:200]
    await update.message.reply_text('Откуда ты? Можно приблизительно.')
    return LOCATION

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['location'] = update.message.text[:200]
    await update.message.reply_text('Какой у тебя опыт участия в конференциях?')
    return EXPERIENCE

async def experience_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['experience'] = update.message.text[:200]
    await update.message.reply_text(
        'Это наши правила. Сможешь их не нарушать?\n\n'
        'К бану могут привести:\n- Нарушение порядка и комфорта участников.\n'
        '- Излишне увлеченное обсуждение спорных тем (политика, религия и т.д.)\n'
        '- Спам, флуд, негатив.\n'
        '- Неактив более 3-х дней.'
    )
    return RULES_AGREEMENT

async def rules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['rules_agreement'] = update.message.text[:200]
    await update.message.reply_text('Почему ты хочешь к нам присоединиться?')
    return JOIN_REASON

async def join_reason_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    join_reason = update.message.text
    user_login = update.message.from_user.username or "Unknown"
    timestamp = datetime.now().isoformat(timespec='seconds')

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO surveys (user_id, login, age, location, experience, rules_agreement, join_reason, status, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            update.message.from_user.id,
            user_login,
            context.user_data['age'],
            context.user_data['location'],
            context.user_data['experience'],
            context.user_data['rules_agreement'],
            join_reason,
            'NEW',
            timestamp
        ))
        conn.commit()

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=f"Новая анкета от @{user_login}")
        except Exception as e:
            print(f"Не удалось отправить сообщение админу {admin_id}: {e}")

    await context.bot.send_message(
        chat_id=5146489793,
        text=(
            f"Новая анкета заполнена!\n\n"
            f"Логин: @{user_login}\n"
            f"Возраст: {context.user_data['age']}\n"
            f"Местоположение: {context.user_data['location']}\n"
            f"Опыт: {context.user_data['experience']}\n"
            f"Согласие с правилами: {context.user_data['rules_agreement']}\n"
            f"Причина присоединения: {join_reason}"
        )
    )

    await update.message.reply_text('Спасибо за заполнение анкеты! Мы ответим тебе в течение трёх часов.')
    return ConversationHandler.END

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        if update.message:
            await update.message.reply_text("Вы не являетесь администратором.")
        elif update.callback_query:
            await update.callback_query.answer("Вы не являетесь администратором.", show_alert=True)
        return

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM surveys WHERE status = "NEW"')
        new_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM surveys WHERE status = "REJECTED"')
        rejected_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM surveys WHERE status = "APPROVED"')
        approved_count = cursor.fetchone()[0]

    keyboard = [
        [InlineKeyboardButton(f"Новые заявки ({new_count})", callback_data="folder_NEW")],
        [InlineKeyboardButton(f"Отказные заявки ({rejected_count})", callback_data="folder_REJECTED")],
        [InlineKeyboardButton(f"Ранее одобренные ({approved_count})", callback_data="folder_APPROVED")],
    ]
    markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Папки заявок:", reply_markup=markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text("Папки заявок:", reply_markup=markup)

async def admin_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("folder_"):
        status = data.split("_")[1]
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, login FROM surveys WHERE status = ? ORDER BY timestamp DESC', (status,))
            applications = cursor.fetchall()

        if not applications:
            await query.edit_message_text("Заявок в этой категории нет.")
            # Автоматически возвращаем в админ-меню
            await admin(update, context)
            return

        keyboard = [
            [InlineKeyboardButton(f"Заявка {app[0]} от @{app[1]}", callback_data=f"view_{app[0]}")]
            for app in applications
        ]
        await query.edit_message_text(f"Список заявок ({status}):", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("view_"):
        app_id = data.split("_")[1]
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM surveys WHERE id = ?', (app_id,))
            application = cursor.fetchone()

        if application:
            buttons = []
            # Если заявка уже одобрена, то кнопка одобрения не показывается
            if application[8] != "APPROVED":
                buttons.append([InlineKeyboardButton("Отправить ссылку на вступление", callback_data=f"approve_{app_id}")])
                buttons.append([InlineKeyboardButton("Отказ", callback_data=f"reject_{app_id}")])
            else:
                buttons.append([InlineKeyboardButton("Отказ", callback_data=f"reject_{app_id}")])

            await query.edit_message_text(
                f"Заявка №{application[0]}\n\n"
                f"Логин: @{application[2]}\n"
                f"Возраст: {application[3]}\n"
                f"Местоположение: {application[4]}\n"
                f"Опыт: {application[5]}\n"
                f"Согласие с правилами: {application[6]}\n"
                f"Причина присоединения: {application[7]}",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

    elif data.startswith("approve_"):
        app_id = data.split("_")[1]
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM surveys WHERE id = ?', (app_id,))
            user_id = cursor.fetchone()[0]
            cursor.execute('UPDATE surveys SET status = "APPROVED" WHERE id = ?', (app_id,))
            conn.commit()

        await context.bot.send_message(chat_id=user_id, text="Будем рады видеть тебя у нас! Ссылка для вступления: https://t.me/+rRs9w_2unJ42OThi")
        await admin(update, context)

    elif data.startswith("reject_"):
        app_id = data.split("_")[1]
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE surveys SET status = "REJECTED" WHERE id = ?', (app_id,))
            conn.commit()

        await admin(update, context)

def main():
    init_db()
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex('^Заполнить анкету$'), fill_form)],
        states={
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age_handler)],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, location_handler)],
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, experience_handler)],
            RULES_AGREEMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, rules_handler)],
            JOIN_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, join_reason_handler)],
        },
        fallbacks=[],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^Хочу прочесть FAQ$'), faq_handler))
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CallbackQueryHandler(admin_button))

    application.run_polling()

if __name__ == '__main__':
    main()

print("Бот запущен.")
