import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from fastapi import FastAPI, Request

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()
app = FastAPI()

# Ваш простой обработчик
@dp.message()
async def echo_handler(message: types.Message):
    await message.answer(f"Бот поддержки на связи! Вы написали: {message.text}")

@app.post("/api")
async def handle_webhook(request: Request):
    # Получаем JSON от Telegram
    json_str = await request.json()
    update = Update.model_validate(json_str, context={"bot": bot})
    # Передаем обновление в Dispatcher
    await dp.feed_update(bot, update)
    return {"status": "ok"}

@app.get("/api")
async def health_check():
    return {"status": "working"}
