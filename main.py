import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from contextlib import asynccontextmanager
import uvicorn

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config from env
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_CHAT_ID = int(os.environ["ADMIN_CHAT_ID"])
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "parrot2026")

# Bot & Dispatcher
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@asynccontextmanager
async def lifespan(app: FastAPI):
    webhook_url = os.environ.get('RAILWAY_PUBLIC_DOMAIN', '')
    if webhook_url:
        await bot.set_webhook(f'https://{webhook_url}/telegram-webhook')
        logger.info(f'Webhook set: https://{webhook_url}/telegram-webhook')
    logger.info('Bot started')
    yield
    await bot.delete_webhook()
    await bot.session.close()
    logger.info('Bot stopped')

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.get("/")
async def root():
    return {"status": "Parrot School Admin Bot is running"}

@app.post("/form")
async def receive_form(request: Request):
    """Endpoint що приймає заявки з сайту"""
    try:
        data = await request.json()
    except Exception:
        return {"ok": False, "error": "Invalid JSON"}

    # Перевіряємо secret
    secret = data.get("secret", "")
    if secret != WEBHOOK_SECRET:
        return {"ok": False, "error": "Unauthorized"}

    name = data.get("name", "—")
    phone = data.get("phone", "—")
    message = data.get("message", "—")
    form_type = data.get("type", "Запис")
    child_age = data.get("child_age", "—")

    text = (
        f"🦜 <b>НОВА ЗАЯВКА — Parrot School</b>\n\n"
        f"📋 <b>Тип:</b> {form_type}\n"
        f"👤 <b>Ім'я:</b> {name}\n"
        f"📞 <b>Телефон:</b> {phone}\n"
        f"👶 <b>Вік дитини:</b> {child_age}\n"
        f"💬 <b>Повідомлення:</b> {message}\n\n"
        f"⏰ Заявка надійшла щойно"
    )

    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return {"ok": False, "error": str(e)}

@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    """Webhook від Telegram"""
    data = await request.json()
    update = types.Update(**data)
    await dp.feed_update(bot=bot, update=update)
    return {"ok": True}

# Telegram команди
@dp.message(lambda m: m.text == "/start")
async def cmd_start(message: types.Message):
    if message.chat.id != ADMIN_CHAT_ID:
        return
    await message.answer(
        "🦜 <b>Parrot School Admin Bot</b>\n\n"
        "Я буду надсилати тобі заявки з сайту.\n\n"
        "/status — статус бота\n"
        "/test — тестова заявка"
    )

@dp.message(lambda m: m.text == "/status")
async def cmd_status(message: types.Message):
    if message.chat.id != ADMIN_CHAT_ID:
        return
    await message.answer("✅ Бот працює. Чекаю заявки з сайту.")

@dp.message(lambda m: m.text == "/test")
async def cmd_test(message: types.Message):
    if message.chat.id != ADMIN_CHAT_ID:
        return
    await message.answer(
        "🦜 <b>НОВА ЗАЯВКА — Parrot School</b>\n\n"
        "📋 <b>Тип:</b> Тестова заявка\n"
        "👤 <b>Ім'я:</b> Тест Тестович\n"
        "📞 <b>Телефон:</b> +380991234567\n"
        "👶 <b>Вік дитини:</b> 8 років\n"
        "💬 <b>Повідомлення:</b> Хочу записати дитину\n\n"
        "⏰ Тестова заявка"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
