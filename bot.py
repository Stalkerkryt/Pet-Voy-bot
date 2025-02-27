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
last_feed_time = {}  # Новый словарь для хранения времени последнего кормления

# ID вашей группы (замените на реальный ID вашей группы)
GROUP_CHAT_ID = '-1002422843451'  # Замените на ваш реальный ID группы

# Логирование в группу
async def log_to_group(message: str):
    try:
        # Отправляем лог в группу
        await bot.send_message(GROUP_CHAT_ID, message)
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в группу: {e}")

# Логирование
logger = logging.getLogger('aiogram')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)

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

# Функция для логирования любых сообщений
async def log_user_message(user_id, user_name, message_text, date):
    log_message = f"User: {user_name} (ID: {user_id})\n" \
                  f"Message: {message_text}\n" \
                  f"Date: {date}\n"
    await log_to_group(log_message)

# Команда /start
@dp.message(Command("start"))
async def start_command(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    if user_id in user_data:
        await message.answer("Вы уже начали настройку бота. Используйте /reset для сброса.")
        return
    user_data[user_id] = {"animal": None, "interval": None, "feed_times": [], "daily_limit": None, "active": True}
    user_data[user_id]["active"] = True
    await message.answer("Привет! Выберите животное, за которым будем ухаживать:", reply_markup=animal_choice_kb)
    # Логирование
    await log_user_message(user_id, user_name, message.text, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# Выбор животного
@dp.message(lambda message: message.text in ["🐱 Кот", "🐶 Собака"])
async def set_animal(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    animal = "кот" if "Кот" in message.text else "собака"
    user_data[user_id]["animal"] = animal
    await message.answer(f"Вы выбрали {animal}! 🐾 Теперь я помогу вам с уходом за ним.\nКак часто нужно кормить?", reply_markup=feeding_interval_kb)
    # Логирование
    await log_user_message(user_id, user_name, message.text, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# Обработка выбора интервала кормления
@dp.message(lambda message: message.text.startswith("Каждые "))
async def set_feeding_interval(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    interval = int(message.text.split()[1])
    user_data[user_id]["interval"] = interval
    await message.answer("Отлично! Теперь выберите, сколько раз в день кормить.", reply_markup=feeding_times_kb)
    # Логирование
    await log_user_message(user_id, user_name, message.text, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# Обработка выбора количества кормлений
@dp.message(lambda message: message.text in ["3 раза", "4 раза", "5 раз", "6 раз"])
async def set_daily_limit(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    limit = int(message.text.split()[0])
    user_data[user_id]["daily_limit"] = limit
    await message.answer(f"Принято! Буду напоминать {limit} раз в день.", reply_markup=main_menu_kb)
    await bot.send_message(user_id, "Время покормить кота! 🐱🥣", reply_markup=confirm_kb)
    # Логирование
    await log_user_message(user_id, user_name, message.text, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    await schedule_feeding_reminder(user_id)

# Подтверждение кормления
@dp.message(lambda message: message.text == "✅ Покормил кота")
async def confirm_feeding(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    now = datetime.now().replace(second=0, microsecond=0)

    # Проверяем, если прошло меньше 5 секунд с последнего нажатия
    if user_id in last_feed_time and now - last_feed_time[user_id] < timedelta(seconds=5):
        await message.answer("Пожалуйста, подождите немного перед повторным нажатием.")
        return

    # Запрещаем нажатие повторно в течение 5 секунд
    last_feed_time[user_id] = now

    if len(user_data[user_id]["feed_times"]) >= user_data[user_id]["daily_limit"]:
        await message.answer("Сегодня кот уже ел достаточно! 🐱 Больше не буду напоминать до завтра.")
        return

    user_data[user_id]["feed_times"].append(now)
    await message.answer(f"Записал! Кот был накормлен в {now.strftime('%H:%M')}.", reply_markup=confirm_kb)
    # Логирование
    await log_user_message(user_id, user_name, message.text, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# Команда /status
@dp.message(Command("status"))
async def show_status(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    if not user_data[user_id]["feed_times"]:
        await message.answer("Сегодня кот ещё не ел. 😿")
        return

    feed_times = [t.strftime('%H:%M') for t in user_data[user_id]["feed_times"]]
    await message.answer(f"🍽 Кормления за сегодня:\n" + "\n".join([f"🕙 {t}" for t in feed_times]))
    # Логирование
    await log_user_message(user_id, user_name, message.text, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# Команда /reset
@dp.message(Command("reset"))
async def reset_confirm(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    await message.answer("⚠ Вы уверены, что хотите сбросить все настройки?\nЭто удалит все данные и начнёт заново.", reply_markup=confirm_reset_kb)
    # Логирование
    await log_user_message(user_id, user_name, message.text, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@dp.message(lambda message: message.text == "✅ Да, сбросить")
async def reset_bot(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_data[user_id] = {"animal": None, "interval": None, "feed_times": [], "daily_limit": None, "active": True}
    await message.answer("Настройки сброшены! 🌀 Начнём заново.\nВыберите животное:", reply_markup=animal_choice_kb)
    # Логирование
    await log_user_message(user_id, user_name, message.text, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@dp.message(lambda message: message.text == "❌ Отмена")
async def cancel_reset(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    await message.answer("Сброс отменён.", reply_markup=main_menu_kb)
    # Логирование
    await log_user_message(user_id, user_name, message.text, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# Команда /stop
@dp.message(Command("stop"))
async def stop_bot(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_data[user_id]["active"] = False
    await message.answer("❌ Напоминания отключены! Если передумаете, отправьте /start.", reply_markup=main_menu_kb)
    # Логирование
    await log_user_message(user_id, user_name, message.text, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# Команда /help
@dp.message(Command("help"))
async def help_command(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    await message.answer(
        "Вот список доступных команд:\n"
        "/start - Начать взаимодействие с ботом\n"
        "/status - Узнать статус кормления\n"
        "/reset - Сбросить настройки\n"
        "/stop - Остановить напоминания\n"
        "/help - Показать это сообщение\n"
    )
    # Логирование
    await log_user_message(user_id, user_name, message.text, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

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
