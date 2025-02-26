@dp.message(Command("start"))
async def start_command(message: Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"interval": None, "feed_times": [], "daily_limit": None, "active": True}
    
    # Если бот выключен командой /stop, включаем его обратно
    user_data[user_id]["active"] = True

    await message.answer("Привет! Как часто нужно кормить кота?", reply_markup=feeding_interval_kb)

@dp.message(Command("reset"))
async def reset_bot(message: Message):
    user_id = message.from_user.id
    user_data[user_id] = {"interval": None, "feed_times": [], "daily_limit": None, "active": True}
    await message.answer("Настройки сброшены! 🌀 Начнём заново.\nКак часто нужно кормить кота?", reply_markup=feeding_interval_kb)

@dp.message(Command("stop"))
async def stop_bot(message: Message):
    user_id = message.from_user.id
    if user_id in user_data:
        user_data[user_id]["active"] = False
        await message.answer("❌ Напоминания отключены! Если передумаете, отправьте /start.")
    else:
        await message.answer("Бот уже выключен.")

async def schedule_feeding_reminder(user_id):
    while True:
        await asyncio.sleep(60)  

        # Проверяем, активен ли бот для пользователя
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
