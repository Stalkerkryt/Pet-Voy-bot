import asyncio
import logging
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

# Загружаем токен
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Создаём бота и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Храним данные пользователей (в памяти, потом можно сделать БД)
user_data = {}

# Клавиатура для выбора интервала кормления
feeding_interval_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Каждые 2 часа"), KeyboardButton(text="Каждые 3 часа")],
        [KeyboardButton(text="Каждые 4 часа"), KeyboardButton(text="Каждые 5 часов")]
    ],
    resize_keyboard=True
)

# Клавиатура с кнопкой подтверждения кормления
confirm_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="✅ Покормил кота")]],
    resize_keyboard=True
)

# Команда /start
@dp.message(Command("start"))
async def start_command(message: Message):
    user_id = message.from_user.id
    user_data[user_id] = {
        "interval": None,
        "feed_times": []
    }
    await message.answer("Привет! Как часто нужно кормить кота?", reply_markup=feeding_interval_kb)

# Обработка выбора интервала кормления
@dp.message(lambda message: message.text.startswith("Каждые "))
async def set_feeding_interval(message: Message):
    user_id = message.from_user.id
    interval = int(message.text.split()[1])  # Извлекаем число из текста "Каждые X часов"
    user_data[user_id]["interval"] = interval
    await message.answer(f"Отлично! Буду напоминать каждые {interval} часа.", reply_markup=confirm_kb)
    await schedule_feeding_reminder(user_id)

# Обработка подтверждения кормления
@dp.message(lambda message: message.text == "✅ Покормил кота")
async def confirm_feeding(message: Message):
    user_id = message.from_user.id
    now = datetime.now()

    # Если кормлений сегодня ещё не было, создаём список
    if "feed_times" not in user_data[user_id]:
        user_data[user_id]["feed_times"] = []

    # Записываем время кормления
    user_data[user_id]["feed_times"].append(now)

    await message.answer(f"Записал! Кот был накормлен в {now.strftime('%H:%M')}.", reply_markup=confirm_kb)

# Команда /status (показывает кормления за день)
@dp.message(Command("status"))
async def show_status(message: Message):
    user_id = message.from_user.id
    if "feed_times" not in user_data[user_id] or not user_data[user_id]["feed_times"]:
        await message.answer("Сегодня кот ещё не ел. 😿")
        return

    # Формируем список кормлений за день
    feed_times = [t.strftime('%H:%M') for t in user_data[user_id]["feed_times"]]
    await message.answer(f"🍽 Кормления за сегодня:\n" + "\n".join([f"🕙 {t}" for t in feed_times]))

# Функция отправки напоминания о кормлении
async def schedule_feeding_reminder(user_id):
    while True:
        await asyncio.sleep(60)  # Проверка каждые 60 секунд

        if user_id not in user_data or user_data[user_id]["interval"] is None:
            continue  # Если нет данных, пропускаем

        now = datetime.now()
        feed_times = user_data[user_id]["feed_times"]

        # Проверяем, было ли кормление недавно
        if feed_times and (now - feed_times[-1]) < timedelta(hours=user_data[user_id]["interval"]):
            continue  # Если кот недавно ел, не напоминаем

        # Отправляем напоминание
        await bot.send_message(user_id, "Время покормить кота! 🐱🥣", reply_markup=confirm_kb)

# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
