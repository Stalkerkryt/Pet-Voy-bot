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

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Клавиатуры
animal_choice_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🐱 Кот"), KeyboardButton(text="🐶 Собака")],
    ],
    resize_keyboard=True
)

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

main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/status"), KeyboardButton(text="/help")],
        [KeyboardButton(text="/reset"), KeyboardButton(text="/stop")]
    ],
    resize_keyboard=True
)

confirm_reset_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Да, сбросить"), KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True
)

# Команда /start
@dp.message(Command("start"))
async def start_command(message: Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"animal": None, "interval": None, "feed_times": [], "daily_limit": None, "active": True}

    user_data[user_id]["active"] = True
    await message.answer("Привет! Выберите животное, за которым будем ухаживать:", reply_markup=animal_choice_kb)
    
    # Логируем информацию о старте
    logger.info(f"/start команда. Пользователь {message.from_user.full_name} (ID: {user_id}) начал работу с ботом.")

# Выбор животного
@dp.message(lambda message: message.text in ["🐱 Кот", "🐶 Собака"])
async def set_animal(message: Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"animal": None, "interval": None, "feed_times": [], "daily_limit": None, "active": True}
    animal = "кот" if "Кот" in message.text else "собака"
    user_data[user_id]["animal"] = animal
    await message.answer(f"Вы выбрали {animal}! 🐾 Теперь я помогу вам с уходом за ним.\nКак часто нужно кормить?", reply_markup=feeding_interval_kb)


    # Логируем выбор животного
    logger.info(f"Пользователь {message.from_user.full_name} (ID: {user_id}) выбрал животное: {animal}.")

# Обработка выбора интервала кормления
@dp.message(lambda message: message.text.startswith("Каждые "))
async def set_feeding_interval(message: Message):
    user_id = message.from_user.id
    interval = int(message.text.split()[1])
    user_data[user_id]["interval"] = interval
    await message.answer("Отлично! Теперь выберите, сколько раз в день кормить.", reply_markup=feeding_times_kb)

    # Логируем выбор интервала
    logger.info(f"Пользователь {message.from_user.full_name} (ID: {user_id}) выбрал интервал кормления: каждые {interval} часа.")

# Обработка выбора количества кормлений
@dp.message(lambda message: message.text in ["3 раза", "4 раза", "5 раз", "6 раз"])
async def set_daily_limit(message: Message):
    user_id = message.from_user.id
    limit = int(message.text.split()[0])
    user_data[user_id]["daily_limit"] = limit

    await message.answer(f"Принято! Буду напоминать {limit} раз в день.", reply_markup=main_menu_kb)
    await bot.send_message(user_id, "Время покормить кота! 🐱🥣", reply_markup=confirm_kb)

    # Логируем выбор количества кормлений
    logger.info(f"Пользователь {message.from_user.full_name} (ID: {user_id}) выбрал количество кормлений: {limit} раз в день.")

# Подтверждение кормления
@dp.message(lambda message: message.text == "✅ Покормил кота")
async def confirm_feeding(message: Message):
    user_id = message.from_user.id
    now = datetime.now().replace(second=0, microsecond=0)

    if len(user_data[user_id]["feed_times"]) >= user_data[user_id]["daily_limit"]:
        await message.answer("Сегодня кот уже ел достаточно! 🐱 Больше не буду напоминать до завтра.")
        return

    user_data[user_id]["feed_times"].append(now)
    await message.answer(f"Записал! Кот был накормлен в {now.strftime('%H:%M')}.", reply_markup=confirm_kb)

    # Логируем кормление
    logger.info(f"Пользователь {message.from_user.full_name} (ID: {user_id}) покормил кота в {now.strftime('%H:%M')}.")

# Команда /status
@dp.message(Command("status"))
async def show_status(message: Message):
    user_id = message.from_user.id
    if not user_data[user_id]["feed_times"]:
        await message.answer("Сегодня кот ещё не ел. 😿")
        return

    feed_times = [t.strftime('%H:%M') for t in user_data[user_id]["feed_times"]]
    await message.answer(f"🍽 Кормления за сегодня:\n" + "\n".join([f"🕙 {t}" for t in feed_times]))

    # Логируем запрос статуса
    logger.info(f"Пользователь {message.from_user.full_name} (ID: {user_id}) запросил статус кормлений.")

# Команда /reset
@dp.message(Command("reset"))
async def reset_confirm(message: Message):
    await message.answer("⚠ Вы уверены, что хотите сбросить все настройки?\nЭто удалит все данные и начнёт заново.", reply_markup=confirm_reset_kb)

@dp.message(lambda message: message.text == "✅ Да, сбросить")
async def reset_bot(message: Message):
    user_id = message.from_user.id
    user_data[user_id] = {"animal": None, "interval": None, "feed_times": [], "daily_limit": None, "active": True}
    await message.answer("Настройки сброшены! 🌀 Начнём заново.\nВыберите животное:", reply_markup=animal_choice_kb)

    # Логируем сброс настроек
    logger.info(f"Пользователь {message.from_user.full_name} (ID: {user_id}) сбросил настройки.")

@dp.message(lambda message: message.text == "❌ Отмена")
async def cancel_reset(message: Message):
    await message.answer("Сброс отменён.", reply_markup=main_menu_kb)

# Команда /stop
@dp.message(Command("stop"))
async def stop_bot(message: Message):
    user_id = message.from_user.id
    user_data[user_id]["active"] = False
    await message.answer("❌ Напоминания отключены! Если передумаете, отправьте /start.", reply_markup=main_menu_kb)

    # Логируем остановку бота
    logger.info(f"Пользователь {message.from_user.full_name} (ID: {user_id}) остановил напоминания.")

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
