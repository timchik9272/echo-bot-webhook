import os
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Update
from fastapi import FastAPI, Request

# Загружаем секретные переменные из окружения Vercel
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Vercel передает переменные как строки, поэтому конвертируем ID в число
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# 1. Обработка ответов админа
@dp.message(F.chat.id == ADMIN_ID, F.reply_to_message)
async def admin_reply_handler(message: types.Message):
    # Пытаемся вытащить текст или подпись к медиа из сообщения, на которое отвечает админ
    replied_msg = message.reply_to_message
    original_text = replied_msg.text or replied_msg.caption or ""
    
    # Ищем хештег с ID пользователя
    match = re.search(r"#id(\d+)", original_text)
    if match:
        user_id = int(match.group(1))
        try:
            # Копируем ответ админа пользователю (поддерживает текст, фото, видео, файлы)
            await message.copy_to(chat_id=user_id)
            await message.reply("✅ Ответ успешно отправлен пользователю.")
        except Exception as e:
            await message.reply(f"❌ Ошибка отправки. Возможно, пользователь заблокировал бота.\nТекст ошибки: {e}")
    else:
        await message.reply("⚠️ Не удалось найти #id пользователя в сообщении. Убедитесь, что отвечаете на пересланное ботом сообщение.")

# 2. Обработка команды /start от пользователей
@dp.message(F.text == "/start")
async def start_command(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Привет, Админ! Я готов пересылать тебе обращения. Просто делай Reply на сообщения пользователей, чтобы ответить им./nВерсия бота: 2")
    else:
        await message.answer("Здравствуйте! Напишите ваш вопрос или отправьте файл, и поддержка ответит вам в ближайшее время. ВНИМАНИЕ! ЭТО НЕ ПОДДЕРЖКА ТЕЛЕГРАММА.")

# 3. Обработка всех остальных сообщений от пользователей (текст, фото, видео, документы)
@dp.message(F.chat.id != ADMIN_ID)
async def user_message_handler(message: types.Message):
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "Без юзернейма"
    
    # Формируем подпись с ID для админа
    caption_appendix = f"\n\nОт: {username} | #id{user_id}"
    
    try:
        if message.text:
            # Если это просто текст
            await bot.send_message(
                chat_id=ADMIN_ID, 
                text=f"{message.text}{caption_appendix}"
            )
        else:
            # Если это медиафайл (фото, видео, голосовое, документ)
            original_caption = message.caption or ""
            new_caption = f"{original_caption}{caption_appendix}"
            
            await bot.copy_message(
                chat_id=ADMIN_ID,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
                caption=new_caption
            )
        await message.answer("✅ Ваше сообщение передано в поддержку. Ожидайте ответа.")
    except Exception as e:
        await message.answer("❌ Произошла ошибка при отправке сообщения.")

# 4. Настройка Webhook для Vercel
@app.post("/api")
async def handle_webhook(request: Request):
    try:
        json_str = await request.json()
        update = Update.model_validate(json_str, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        pass # Игнорируем ошибки сериализации, чтобы Vercel не падал
    return {"status": "ok"}

@app.get("/api")
async def health_check():
    return {"status": "working", "admin_id_set": bool(ADMIN_ID)}
