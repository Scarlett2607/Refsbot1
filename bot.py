import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
import sqlite3

# Логирование
logging.basicConfig(level=logging.INFO)

# === ТОЛЬКО ЭТИ СТРОКИ ТЕБЕ НУЖНО ЗАМЕНИТЬ ===
BOT_TOKEN = "7720693647:AAGtXjfF3aQzb2IAEdf4mWHwwCXfNRwDlG0"  # Замените на токен вашего бота
CHANNEL_LINK = "https://t.me/+YX-S8AscKHNmZmYy"   # Замените на ваш канал
# ======================================================

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Подключение к БД
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

# Создание таблиц
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    referrals INTEGER DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS referrals_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER,
    referred_id INTEGER UNIQUE
)
""")
conn.commit()

# --- Функции работы с БД ---
def add_user_if_not_exists(user_id: int, username: str):
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()

def add_referral(referrer_id: int, referred_id: int):
    if referrer_id == referred_id:
        return
    cursor.execute("SELECT 1 FROM referrals_log WHERE referred_id = ?", (referred_id,))
    if cursor.fetchone():
        return
    cursor.execute("INSERT INTO referrals_log (referrer_id, referred_id) VALUES (?, ?)", (referrer_id, referred_id))
    cursor.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id = ?", (referrer_id,))
    conn.commit()

def get_referral_count(user_id: int) -> int:
    cursor.execute("SELECT referrals FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def get_top_referrals(limit: int = 10) -> list:
    cursor.execute("SELECT username, referrals FROM users ORDER BY referrals DESC LIMIT ?", (limit,))
    return cursor.fetchall()

# --- Клавиатура с reply-кнопками ---
def main_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="мои последователи")],
            [KeyboardButton(text="топ рефералов")],
            [KeyboardButton(text="совсем скоро...")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


# --- Обработчики ---
@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "пользователь"

    add_user_if_not_exists(user_id, username)

    args = message.text.split()[1:]  # Получаем параметры из команды /start
    if args:
        referrer_id = args[0]
        if referrer_id.isdigit():
            referrer_id = int(referrer_id)
            if referrer_id != user_id:
                add_referral(referrer_id, user_id)

    text = (
        "измени свою жизнь.\n"
        "всего одно решение.\n"
        "ты скажешь себе спасибо.\n"
        "вся инфа в канале."
    )

    await message.answer(text, reply_markup=main_menu_keyboard())

@dp.message(F.text == "мои последователи")
async def get_link(message: Message):
    bot_username = (await bot.get_me()).username
    user_id = message.from_user.id
    link = f"https://t.me/{bot_username}?start={user_id}"

    referrals = get_referral_count(user_id)

    text = f"твоя реферальная ссылка:\n{link}\n\n"
    text += f"я помог {referrals} людям"

    await message.answer(text)

@dp.message(F.text == "топ рефералов")
async def top_referrals(message: Message):
    top_users = get_top_referrals()
    text = "топ 10 по рефералам:\n\n"
    for idx, (username, count) in enumerate(top_users, 1):
        text += f"{idx}. {username} — {count}\n"

    text += "\nпризы:\n"
    text += "1 место - доступ в scarlett club\n"
    text += "2 место - nft до 50 тон\n"
    text += "3 место - nft до 20 тон\n"
    text += "4-5 места - nft до 10 тон\n"
    text += "6-10 места - мишки\n\n"
    text += "дата окончания есть в канале"

    await message.answer(text)

@dp.message(F.text == "совсем скоро...")
async def go_to_open_channel(message: Message):
    await message.answer(f"совсем скоро -- {CHANNEL_LINK}")

# --- Запуск бота --- 
async def main():
    print("✅ бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())