import asyncio
import logging
import os
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

# Храним выбор пользователя
user_pets = {}

# Клавиатура для выбора животного
choose_pet_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🐱 Кот"), KeyboardButton(text="🐶 Собака")]
    ],
    resize_keyboard=True
)

# Команда /start
@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("Привет! Выберите животное, за которым будем ухаживать:", reply_markup=choose_pet_kb)

# Обработка выбора животного
@dp.message(lambda message: message.text in ["🐱 Кот", "🐶 Собака"])
async def choose_pet(message: Message):
    user_pets[message.from_user.id] = message.text  # Запоминаем выбор пользователя
    if message.text == "🐱 Кот":
        await message.answer("Вы выбрали кота! 🐱 Теперь я помогу вам с уходом за ним.")
    else:
        await message.answer("Вы выбрали собаку! 🐶 Пока функционал для собак в разработке.")

# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
