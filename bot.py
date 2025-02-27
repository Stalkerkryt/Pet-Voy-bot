import asyncio
import logging
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
import requests

# Загружаем токен
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Создаём бота и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Храним данные пользователей
user_data = {}
last_feed_time = {}

# Ваш чат ID для отправки логов в Telegram (найди его, отправив сообщение боту и использовав API для получения ID)
CHAT_ID = "1080331499"

# Функция для отправки логов в Telegram
def send_log(message):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    payload = {'chat_id': CHAT_ID, 'text': message}
    requests.post(url, data=payload)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования
    format='%(asctime)s - %(message)s',  # Формат логов
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Клавиатуры
animal_choice_kb = ReplyKeyboardMarkup(
    keyboard=[ [KeyboardButton(text="🐱 Кот"), KeyboardButton(text="🐶 Собака")], ],
    resize_keyboard=True
)

feeding_interval_kb = ReplyKeyboardMarkup(
    keyboard=[ [KeyboardButton(text="Каждые 2 часа"), KeyboardButton(text="Каждые 3 часа")], 
              [KeyboardButton(text="Каждые 4 часа"), KeyboardButton(text="Каждые 5 часов")] ],
    resize_keyboard=True
)

feeding_times_kb = ReplyKeyboardMarkup(
    keyboard=[ [KeyboardButton(text="3 раза"), KeyboardButton(text="4 раза")], 
              [KeyboardButton(text="5 раз"), KeyboardButton(text="6 раз")] ],
    resize_keyboard=True
)

confirm_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="✅ Покормил кота")]],
    resize_keyboard=True
)

main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[ [KeyboardButton(text="/status"), KeyboardButton(text="/help")], 
              [KeyboardButton(text="/reset"), KeyboardButton(text="/stop")] ],
    resize_keyboard=True
)

confirm_reset_kb = ReplyKeyboardMarkup(
    keyboard=[ [KeyboardButton(text="✅ Да, сбросить"), KeyboardButton(text="❌ Отмена")] ],
    resize_keyboard=True
)

# Логирование всех сообщений
@dp.message_handler()
async def log_message(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    text = message.text
    logger.info(f"User {user_name} (ID: {user_id}) sent a message: {text}")
    send_log(f"User {user_name} (ID: {user_id}) sent a message: {text}")

# Команда /start
@dp.message(Command("start"))
async def start_command(message: Message):
    user_id = message.from_user.id
    if user_id in user_data:
        await message.answer("Вы уже начали настройку бота. Используйте /reset для сброса.")
        return
    user_data[user_id] = {"animal": None, "interval": None, "feed_times": [], "daily_limit": None, "active": True}
    user_data[user_id]["active"] = True
    await message.answer("Привет! Выберите животное, за которым будем ухаживать:", reply_markup=animal_choice_kb)

# Команда /help
@dp.message(Command("help"))
async def help_command(message: Message):
    user_id = message.from_user.id
    await message.answer(
        "Вот список доступных команд:\n"
        "/start - Начать взаимодействие с ботом\n"
        "/status - Узнать статус кормления\n"
        "/reset - Сбросить настройки\n"
        "/stop - Остановить напоминания\n"
        "/help - Показать это сообщение\n"
    )

# Команда /status
@dp.message(Command("status"))
async def show_status(message: Message):
    user_id = message.from_user.id
    if not user_data[user_id]["feed_times"]:
        await message.answer("Сегодня кот ещё не ел. 😿")
        return
    feed_times = [t.strftime('%H:%M') for t in user_data[user_id]["feed_times"]]
    await message.answer(f"🍽 Кормления за сегодня:\n" + "\n".join([f"🕙 {t}" for t in feed_times]))

# Команда /reset
@dp.message(Command("reset"))
async def reset_confirm(message: Message):
    await message.answer("⚠ Вы уверены, что хотите сбросить все настройки?\nЭто удалит все данные и начнёт заново.", reply_markup=confirm_reset_kb)

@dp.message(lambda message: message.text == "✅ Да, сбросить")
async def reset_bot(message: Message):
    user_id = message.from_user.id
    user_data[user_id] = {"animal": None, "interval": None, "feed_times": [], "daily_limit": None, "active": True}
    await message.answer("Настройки сброшены! 🌀 Начнём заново.\nВыберите животное:", reply_markup=animal_choice_kb)

@dp.message(lambda message: message.text == "❌ Отмена")
async def cancel_reset(message: Message):
    await message.answer("Сброс отменён.", reply_markup=main_menu_kb)

# Подтверждение кормления
@dp.message(lambda message: message.text == "✅ Покормил кота")
async def confirm_feeding(message: Message):
    user_id = message.from_user.id
    now = datetime.now().replace(second=0, microsecond=0)

    if user_id in last_feed_time and now - last_feed_time[user_id] < timedelta(seconds=5):
        await message.answer("Пожалуйста, подождите немного перед повторным нажатием.")
        return

    last_feed_time[user_id] = now

    if len(user_data[user_id]["feed_times"]) >= user_data[user_id]["daily_limit"]:
        await message.answer("Сегодня кот уже ел достаточно! 🐱 Больше не буду напоминать до завтра.")
        return

    user_data[user_id]["feed_times"].append(now)
    await message.answer(f"Записал! Кот был накормлен в {now.strftime('%H:%M')}.", reply_markup=confirm_kb)

# Запуск напоминаний
async def schedule_feeding_reminder(user_id):
    while True:
        await asyncio.sleep(60)
        if not user_data[user_id]["active"]:
            continue
        if user_data[user_id]["interval"] is None or user_data[user_id]["daily_limit"] is None:
            continue
        now = datetime.now()
        feed_times = user_data[user_id]["feed_times"]

        if not feed_times:
            user_data[user_id]["feed_times"].append(now)
            await bot.send_message(user_id, "Время покормить кота! 🐱🥣", reply_markup=confirm_kb)
            continue

        if len(feed_times) >= user_data[user_id]["daily_limit"]:
            continue

        last_feed_time = feed_times[-1]
        if now - last_feed_time >= timedelta(hours=user_data[user_id]["interval"]):
            user_data[user_id]["feed_times"].append(now)
            await bot.send_message(user_id, "Время покормить кота! 🐱🥣", reply_markup=confirm_kb)

        if now.hour == 0 and now.minute == 0:
            user_data[user_id]["feed_times"] = []
            await bot.send_message(user_id, "🌅 Новый день! Не забудь покормить кота.", reply_markup=confirm_kb)

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
