import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

# Загружаем токен из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Создаём бота и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Команда /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("Привет! Я бот для ухода за питомцами 🐶🐱. Я помогу напоминать о кормлении, стрижке и визитах к ветеринару!")

# Команда /help
@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer("Доступные команды:\n"
                         "/start - Начать\n"
                         "/help - Помощь\n"
                         "Скоро добавлю напоминания!")

# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
