import os
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
from datetime import datetime

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask приложение для Render
app = Flask(__name__)

# Токен бота (установить в переменных окружения на Render)
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'https://your-app.onrender.com')

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  character_class TEXT,
                  level INTEGER DEFAULT 1,
                  hp INTEGER,
                  max_hp INTEGER,
                  attack INTEGER,
                  defense INTEGER,
                  gold INTEGER DEFAULT 0,
                  exp INTEGER DEFAULT 0,
                  created_at TIMESTAMP)''')
    conn.commit()
    conn.close()

# Проверка регистрации пользователя
def is_user_registered(user_id):
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

# Регистрация пользователя
def register_user(user_id, username, character_class):
    # Характеристики классов
    classes = {
        'warrior': {'hp': 150, 'attack': 25, 'defense': 15},
        'archer': {'hp': 100, 'attack': 30, 'defense': 8},
        'mage': {'hp': 80, 'attack': 35, 'defense': 5}
    }
    
    stats = classes[character_class]
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('''INSERT INTO users 
                 (user_id, username, character_class, hp, max_hp, attack, defense, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (user_id, username, character_class, stats['hp'], stats['hp'], 
               stats['attack'], stats['defense'], datetime.now()))
    conn.commit()
    conn.close()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    if is_user_registered(user_id):
        await update.message.reply_text(
            f"🎮 С возвращением, {username}!\n\n"
            "Ты уже зарегистрирован. Используй команды для игры:\n"
            "/profile - твой профиль\n"
            "/battle - начать битву"
        )
        return
    
    # Приветственное сообщение с выбором класса
    welcome_text = (
        "⚔️ **ДОБРО ПОЖАЛОВАТЬ В RPG ИГРУ!** ⚔️\n\n"
        "Добро пожаловать, искатель приключений! Тебе предстоит выбрать свой путь.\n\n"
        "📜 **КЛАССЫ ПЕРСОНАЖЕЙ:**\n\n"
        "🗡 **ВОИН (Warrior)**\n"
        "├ HP: ❤️❤️❤️ (150)\n"
        "├ Урон: ⚔️⚔️ (25)\n"
        "├ Защита: 🛡🛡 (15)\n"
        "└ Особенность: Высокая живучесть, средний урон\n\n"
        "🏹 **ЛУЧНИК (Archer)**\n"
        "├ HP: ❤️❤️ (100)\n"
        "├ Урон: ⚔️⚔️⚔️ (30)\n"
        "├ Защита: 🛡 (8)\n"
        "└ Особенность: Высокий урон, средняя защита\n\n"
        "🔮 **МАГ (Mage)**\n"
        "├ HP: ❤️ (80)\n"
        "├ Урон: ⚔️⚔️⚔️⚔️ (35)\n"
        "├ Защита: 🛡 (5)\n"
        "└ Особенность: Максимальный урон, низкая защита\n\n"
        "⚡ **Выбирай класс и начинай своё приключение!**"
    )
    
    keyboard = [
        [InlineKeyboardButton("🏹 Лучник", callback_data='class_archer'),
         InlineKeyboardButton("🗡 Воин", callback_data='class_warrior')],
        [InlineKeyboardButton("🔮 Маг", callback_data='class_mage')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

# Обработка выбора класса
async def class_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name
    
    # Извлечение класса из callback_data
    character_class = query.data.split('_')[1]
    
    # Регистрация пользователя
    register_user(user_id, username, character_class)
    
    class_names = {
        'warrior': '🗡 Воин',
        'archer': '🏹 Лучник',
        'mage': '🔮 Маг'
    }
    
    success_message = (
        f"✅ **РЕГИСТРАЦИЯ ЗАВЕРШЕНА!**\n\n"
        f"Ты выбрал класс: {class_names[character_class]}\n\n"
        f"🎮 Используй команды:\n"
        f"/profile - посмотреть свой профиль\n"
        f"/battle - начать битву\n"
        f"/help - список всех команд"
    )
    
    await query.edit_message_text(success_message, parse_mode='Markdown')

# Команда /profile
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_user_registered(user_id):
        await update.message.reply_text("❌ Ты не зарегистрирован! Используй /start")
        return
    
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    
    class_emoji = {
        'warrior': '🗡',
        'archer': '🏹',
        'mage': '🔮'
    }
    
    profile_text = (
        f"{class_emoji[user[2]]} **ТВО��� ПРОФИЛЬ**\n\n"
        f"👤 Имя: {user[1]}\n"
        f"⭐ Уровень: {user[3]}\n"
        f"❤️ HP: {user[4]}/{user[5]}\n"
        f"⚔️ Атака: {user[6]}\n"
        f"🛡 Защита: {user[7]}\n"
        f"💰 Золото: {user[8]}\n"
        f"✨ Опыт: {user[9]}/100"
    )
    
    await update.message.reply_text(profile_text, parse_mode='Markdown')

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 **СПИСОК КОМАНД:**\n\n"
        "/start - начать игру\n"
        "/profile - твой профиль\n"
        "/battle - начать битву\n"
        "/help - эта справка"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Flask маршруты
@app.route('/')
def index():
    return 'Telegram RPG Bot is running!'

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return 'OK'

# Настройка бота
def setup_application():
    global application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавление обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(class_selection, pattern='^class_'))
    
    return application

# Инициализация при запуске
if __name__ == '__main__':
    init_db()
    setup_application()
    
    # Для локальной разработки
    # application.run_polling()
    
    # Для Render (webhook)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
