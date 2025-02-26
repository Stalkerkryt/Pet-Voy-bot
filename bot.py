import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from dotenv import load_dotenv
import os

# Загрузка токена из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Создание бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Данные пользователей
user_data = {}

# Кнопки для выбора животных
animal_kb = ReplyKeyboardMarkup(resize_keyboard=True)
animal_kb.add(KeyboardButton("🐱 Кот"))
animal_kb.add(KeyboardButton("🐶 Собака"))

# Кнопки для подтверждения кормления
confirm_kb = ReplyKeyboardMarkup(resize_keyboard=True)
confirm_kb.add(KeyboardButton("✅ Покормил кота"))

# Старт бота
@dp.message(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id] = {
        "animal": None,
        "pet_name": None,
        "interval": None,
        "daily_limit": None,
        "feed_times": [],
        "just_reminded": False,
        "active": True
    }
    await message.answer("Привет! Выберите животное, за которым будем ухаживать:", reply_markup=animal_kb)

# Выбор животного
@dp.message(lambda message: message.text in ["🐱 Кот", "🐶 Собака"])
async def choose_animal(message: types.Message):
    user_id = message.from_user.id
    animal = "кот" if "Кот" in message.text else "собака"
    user_data[user_id]["animal"] = animal
    await message.answer(f"Вы выбрали {animal}! 🐾 Теперь я помогу вам с уходом за ним.\nКак зовут вашего питомца?")

# Ввод имени питомца
@dp.message(lambda message: message.text)
async def set_pet_name(message: types.Message):
    user_id = message.from_user.id
    if user_data[user_id]["pet_name"] is None:
        user_data[user_id]["pet_name"] = message.text.strip()
        await message.answer(f"Отлично! Теперь я буду напоминать вам про {user_data[user_id]['pet_name']}!\nКак часто нужно кормить?")
        await message.answer("Выберите интервал кормления в часах (например, 4):")

# Выбор интервала кормления
@dp.message(lambda message: message.text.isdigit())
async def choose_interval(message: types.Message):
    user_id = message.from_user.id
    interval = int(message.text)
    user_data[user_id]["interval"] = interval
    await message.answer("Отлично! Теперь выберите, сколько раз в день кормить питомца (например, 4):")

# Выбор количества кормлений в день
@dp.message(lambda message: message.text.isdigit())
async def choose_daily_limit(message: types.Message):
    user_id = message.from_user.id
    daily_limit = int(message.text)
    user_data[user_id]["daily_limit"] = daily_limit
    await message.answer(f"Принято! Буду напоминать {daily_limit} раз в день.")

    # Запуск напоминаний
    await schedule_feeding_reminder(user_id)

# Запуск напоминаний
async def schedule_feeding_reminder(user_id):
    while True:
        await asyncio.sleep(60)  # Проверяем каждую минуту

        if not user_data[user_id]["active"]:
            continue  # Если бот отключен, ничего не делаем

        if user_data[user_id]["interval"] is None or user_data[user_id]["daily_limit"] is None:
            continue  # Если нет данных о кормлении, ничего не делаем

        now = datetime.now()
        feed_times = user_data[user_id]["feed_times"]

        # Первое напоминание приходит сразу
        if not feed_times:
            await bot.send_message(user_id, f"Время покормить {user_data[user_id]['pet_name']}! 🐱🥣", reply_markup=confirm_kb)
            user_data[user_id]["feed_times"].append(now)  # Запоминаем, что отправили напоминание
            continue

        # Проверяем, кормил ли человек питомца вовремя
        last_feed_time = feed_times[-1]
        time_since_last = (now - last_feed_time).total_seconds() / 60  # Разница в минутах

        # Если достигли дневного лимита – прекращаем напоминания
        if len(feed_times) >= user_data[user_id]["daily_limit"]:
            continue  # Лимит кормлений исчерпан – ждем следующий день

        # Если наступило запланированное время кормления
        if time_since_last >= user_data[user_id]["interval"] * 60:
            await bot.send_message(user_id, f"Время покормить {user_data[user_id]['pet_name']}! 🐱🥣", reply_markup=confirm_kb)
            user_data[user_id]["feed_times"].append(now)  # Запоминаем время напоминания

        # Если человек не покормил вовремя – каждые 10 минут напоминание
        elif time_since_last >= 10 and not user_data[user_id]["just_reminded"]:
            await bot.send_message(user_id, f"⏳ Не забудь покормить {user_data[user_id]['pet_name']}! 🐱🥣", reply_markup=confirm_kb)
            user_data[user_id]["just_reminded"] = True  # Помечаем, что отправили напоминание

        # Как только пользователь кормит питомца – сбрасываем напоминание
        if user_data[user_id]["just_reminded"] and len(feed_times) > 0:
            user_data[user_id]["just_reminded"] = False  # Сбрасываем флаг

# Подтверждение кормления с защитой от случайных нажатий
@dp.message(lambda message: message.text == "✅ Покормил кота")
async def confirm_feeding(message: types.Message):
    user_id = message.from_user.id
    now = datetime.now().replace(second=0, microsecond=0)

    # Если нет лимита на день, игнорируем команду
    if user_data[user_id]["daily_limit"] is None:
        await message.answer("Ты ещё не настроил расписание кормлений. 🛠 Используй /start")
        return

    # Проверка на частоту нажатий (анти-спам)
    if user_data[user_id]["feed_times"]:
        last_feed_time = user_data[user_id]["feed_times"][-1]
        time_since_last = (now - last_feed_time).total_seconds() / 60  # Разница в минутах

        if time_since_last < 10:  # Если прошло меньше 10 минут
            await message.answer("⏳ Пожалуйста, подожди немного перед следующим кормлением!")
            return

    # Записываем кормление
    user_data[user_id]["feed_times"].append(now)
    await message.answer(f"Записал! {user_data[user_id]['pet_name']} был накормлен в {now.strftime('%H:%M')}.", reply_markup=confirm_kb)

# Сброс настроек и очистка всех данных
@dp.message(lambda message: message.text == "/reset")
async def reset_settings(message: types.Message):
    user_id = message.from_user.id

    # Спрашиваем подтверждение сброса
    await message.answer(
        "⚠️ Вы уверены, что хотите сбросить все настройки?\nЭто удалит все данные и начнёт заново.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="✅ Да, сбросить"), KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True,
        )
    )

# Обработка подтверждения сброса
@dp.message(lambda message: message.text == "✅ Да, сбросить")
async def confirm_reset(message: types.Message):
    user_id = message.from_user.id

    # Полный сброс данных
    user_data[user_id] = {
        "active": False,
        "animal": None,
        "pet_name": None,
        "interval": None,
        "daily_limit": None,
        "feed_times": [],
        "just_reminded": False,  # Сбрасываем напоминания
    }

    await message.answer("🌀 Настройки сброшены! 🔄 Начнём заново.\nВыберите животное:", reply_markup=animal_kb)

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
