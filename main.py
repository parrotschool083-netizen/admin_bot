import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from contextlib import asynccontextmanager
import uvicorn
import db
from handlers import client, admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_CHAT_ID = int(os.environ["ADMIN_CHAT_ID"])
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "parrot2026")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = RedisStorage.from_url(REDIS_URL)
dp = Dispatcher(storage=storage)

@asynccontextmanager
async def lifespan(app: FastAPI):
    dp.include_router(client.router)
    dp.include_router(admin.router)
    await db.init_db()
    await bot.set_my_commands([
        types.BotCommand(command="start", description="🦜 Головне меню"),
        types.BotCommand(command="admin", description="👑 Адмін панель"),
    ])
    webhook_url = "adminbot-production-dabe.up.railway.app"
    await bot.set_webhook(f"https://{webhook_url}/telegram-webhook")
    logger.info(f"Webhook set: https://{webhook_url}/telegram-webhook")
    logger.info("Bot started")
    yield
    await bot.delete_webhook()
    await bot.session.close()
    await db.close_db()
    logger.info("Bot stopped")

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
    try:
        data = await request.json()
    except Exception:
        return {"ok": False, "error": "Invalid JSON"}

    secret = data.get("secret", "")
    if secret != WEBHOOK_SECRET:
        return {"ok": False, "error": "Unauthorized"}

    name = data.get("name", "—")
    phone = data.get("phone", "—")
    child_age = data.get("child_age", "—")
    form_type = data.get("type", "Запис")

    async with db.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO requests (name, phone, child_age, type)
            VALUES ($1, $2, $3, $4)
        """, name, phone, child_age, form_type)

    text = (
        f"🦜 <b>НОВА ЗАЯВКА — Parrot School</b>\n\n"
        f"📋 <b>Тип:</b> {form_type}\n"
        f"👤 <b>Ім'я:</b> {name}\n"
        f"📞 <b>Телефон:</b> {phone}\n"
        f"👶 <b>Вік дитини:</b> {child_age}\n\n"
        f"⏰ Заявка надійшла щойно"
    )

    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"ok": False, "error": str(e)}

@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = types.Update(**data)
    await dp.feed_update(bot=bot, update=update)
    return {"ok": True}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
