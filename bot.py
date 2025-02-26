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

# Храним данные пользователей
user_data = {}

# Клавиатуры
feeding_interval_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Каждые 2 часа"), KeyboardButton(text="Каждые 3 часа")],
        [KeyboardButton(text="Каждые 4 часа"), KeyboardButton(text="Каждые 5 часов")]
    ],
    resize_keyboard=True
)

feeding_times_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="3 раза"), KeyboardButton(text="4 раза")],
        [KeyboardButton(text="5 раз"), KeyboardButton(text="6 раз")]
    ],
    resize_keyboard=True
)

confirm_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="✅ Покормил кота")]],
    resize_keyboard=True
)

# Команда /start
@dp.message(Command("start"))
async def start_command(message: Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"interval": None, "feed_times": [], "daily_limit": None, "active": True}

    user_data[user_id]["active"] = True
    await message.answer("Привет! Как часто нужно кормить кота?", reply_markup=feeding_interval_kb)

# Команда /reset (сброс настроек)
@dp.message(Command("reset"))
async def reset_bot(message: Message):
    user_id = message.from_user.id
    user_data[user_id] = {"interval": None, "feed_times": [], "daily_limit": None, "active": True}
    await message.answer("Настройки сброшены! 🌀 Начнём заново.\nКак часто нужно кормить кота?", reply_markup=feeding_interval_kb)

# Команда /stop (отключить напоминания)
@dp.message(Command("stop"))
async def stop_bot(message: Message):
    user_id = message.from_user.id
    if user_id in user_data:
        user_data[user_id]["active"] = False
        await message.answer("❌ Напоминания отключены! Если передумаете, отправьте /start.")
    else:
        await message.answer("Бот уже выключен.")

# Обработка выбора интервала кормления
@dp.message(lambda message: message.text.startswith("Каждые "))
async def set_feeding_interval(message: Message):
    user_id = message.from_user.id
    interval = int(message.text.split()[1])  
    user_data[user_id]["interval"] = interval
    await message.answer("Отлично! Теперь выберите, сколько раз в день кормить кота.", reply_markup=feeding_times_kb)

# Обработка выбора количества кормлений
@dp.message(lambda message: message.text.endswith("раз"))
async def set_daily_limit(message: Message):
    user_id = message.from_user.id
    limit = int(message.text.split()[0])  
    user_data[user_id]["daily_limit"] = limit
    await message.answer(f"Принято! Буду напоминать {limit} раз в день.", reply_markup=confirm_kb)
    await schedule_feeding_reminder(user_id)

# Подтверждение кормления
@dp.message(lambda message: message.text == "✅ Покормил кота")
async def confirm_feeding(message: Message):
    user_id = message.from_user.id
    now = datetime.now().replace(second=0, microsecond=0)

    if "feed_times" not in user_data[user_id]:
        user_data[user_id]["feed_times"] = []

    if len(user_data[user_id]["feed_times"]) >= user_data[user_id]["daily_limit"]:
        await message.answer("Сегодня кот уже ел достаточно! 🐱 Больше не буду напоминать до завтра.")
        return

    user_data[user_id]["feed_times"].append(now)
    await message.answer(f"Записал! Кот был накормлен в {now.strftime('%H:%M')}.", reply_markup=confirm_kb)

# Команда /status (показывает кормления за день)
@dp.message(Command("status"))
async def show_status(message: Message):
    user_id = message.from_user.id
    if "feed_times" not in user_data[user_id] or not user_data[user_id]["feed_times"]:
        await message.answer("Сегодня кот ещё не ел. 😿")
        return

    feed_times = [t.strftime('%H:%M') for t in user_data[user_id]["feed_times"]]
    await message.answer(f"🍽 Кормления за сегодня:\n" + "\n".join([f"🕙 {t}" for t in feed_times]))

# Запуск напоминаний
async def schedule_feeding_reminder(user_id):
    while True:
        await asyncio.sleep(60)  

        if user_id not in user_data or not user_data[user_id]["active"]:
            continue  

        if user_data[user_id]["interval"] is None or user_data[user_id]["daily_limit"] is None:
            continue  

        now = datetime.now()
        feed_times = user_data[user_id]["feed_times"]

        if len(feed_times) >= user_data[user_id]["daily_limit"]:
            continue  

        if feed_times and (now - feed_times[-1]) < timedelta(hours=user_data[user_id]["interval"]):
            continue  

        await bot.send_message(user_id, "Время покормить кота! 🐱🥣", reply_markup=confirm_kb)

        if now.hour == 0 and now.minute == 0:
            user_data[user_id]["feed_times"] = []

# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
