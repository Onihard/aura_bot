import sqlite3
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler
)

# Токен вашего бота
TOKEN = "7828229702:AAGu34KJ_-GZCXSMSf26ASMNaocjSbnMU7M"

# Состояния для ConversationHandler
AGE, LOCATION, EXPERIENCE, RULES_AGREEMENT, JOIN_REASON = range(5)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('surveys.db')
    cursor = conn.cursor()

    # Создаем таблицу, если она не существует
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS surveys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            login TEXT,
            age TEXT,
            location TEXT,
            experience TEXT,
            rules_agreement TEXT,
            join_reason TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Заполнить анкету"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        'Привет! Спасибо за интерес к нашей конференции. Здесь можно заполнить анкету для вступления, это займет пару минут. Анкеты рассматриваются вручную в течение трех часов.',
        reply_markup=reply_markup
    )

# Обработчик кнопки "Заполнить анкету"
async def fill_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Пожалуйста, введите ваш возраст:', reply_markup=ReplyKeyboardRemove())
    return AGE

# Обработчик возраста
async def age_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    age = update.message.text[:200]  # Ограничение в 200 символов
    context.user_data['age'] = age
    await update.message.reply_text('Откуда ты? Можно приблизительно.')
    return LOCATION

# Обработчик местоположения
async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.text[:200]  # Ограничение в 200 символов
    context.user_data['location'] = location
    await update.message.reply_text('Какой у тебя опыт участия в конференциях?')
    return EXPERIENCE

# Обработчик опыта
async def experience_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    experience = update.message.text[:200]  # Ограничение в 200 символов
    context.user_data['experience'] = experience
    await update.message.reply_text('Это наши правила. Сможешь их не нарушать?\n\nК бану могут привести:\n- Нарушение порядка и комфорта участников.\n- Излишне увлеченное обсуждение спорных тем (политика, религия и т.д.)\n- Спам, флуд, негатив.\n- Неактив более 3-х дней.')
    return RULES_AGREEMENT

# Обработчик согласия с правилами
async def rules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rules_agreement = update.message.text[:500]  # Ограничение в 500 символов
    context.user_data['rules_agreement'] = rules_agreement
    await update.message.reply_text('Почему ты хочешь к нам присоединиться?')
    return JOIN_REASON

# Обработчик причины присоединения
async def join_reason_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    join_reason = update.message.text  # Без ограничения по длине
    user_login = update.message.from_user.username
    if user_login is None:
        user_login = "Unknown"

    # Сохранение данных в базу данных
    conn = sqlite3.connect('surveys.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO surveys (user_id, login, age, location, experience, rules_agreement, join_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (update.message.from_user.id, user_login, context.user_data['age'], context.user_data['location'], context.user_data['experience'], context.user_data['rules_agreement'], join_reason))
    conn.commit()
    conn.close()

    # Отправка данных вам в личные сообщения
    await context.bot.send_message(
        chat_id=5146489793,  # Замените на ваш числовой идентификатор
        text=f"Новая анкета заполнена!\n\n"
             f"Логин: @{user_login}\n"
             f"Возраст: {context.user_data['age']}\n"
             f"Местоположение: {context.user_data['location']}\n"
             f"Опыт: {context.user_data['experience']}\n"
             f"Согласие с правилами: {context.user_data['rules_agreement']}\n"
             f"Причина присоединения: {join_reason}"
    )

    await update.message.reply_text('Спасибо за заполнение анкеты! Мы ответим тебе в течение трёх часов (обычно быстрее).')
    return ConversationHandler.END

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
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
