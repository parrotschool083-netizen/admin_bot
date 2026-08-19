import os
import logging
import asyncio
import hashlib
import time
import aiohttp
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
KEYCRM_API_KEY = os.environ.get("KEYCRM_API_KEY", "")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = RedisStorage.from_url(REDIS_URL)
dp = Dispatcher(storage=storage)

@asynccontextmanager
async def lifespan(app: FastAPI):
    dp.include_router(client.router)
    dp.include_router(admin.router)
    await db.init_db()
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Головне меню"),
        types.BotCommand(command="admin", description="Адмін панель"),
    ])
    await bot.set_webhook(
        url="https://adminbot-production-dabe.up.railway.app/telegram-webhook",
        drop_pending_updates=True,
        secret_token=WEBHOOK_SECRET
    )
    logger.info("Webhook set")
    yield
    await bot.session.close()
    await db.close_db()
    logger.info("Bot stopped")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

@app.get("/")
async def root():
    return {"status": "Parrot School Admin Bot is running"}

@app.post("/form")
async def receive_form(request: Request):
    import time as _time
    _rid = f"{id(request)}-{_time.time()}"
    logger.info(f"[FORM] request_id={_rid}")
    try:
        data = await request.json()
    except Exception:
        return {"ok": False, "error": "Invalid JSON"}

    secret = data.get("secret", "")
    if secret != WEBHOOK_SECRET:
        return {"ok": False, "error": "Unauthorized"}

    name = data.get("name", "-")
    phone = data.get("phone", "-")
    child_age = data.get("child_age", "-")
    form_type = data.get("type", "Запис")

    # Дедублікація — перевіряємо чи є такий самий запит за останні 60 секунд
    import hashlib as _hs
    dedup_key = f"form:{_hs.md5(f'{name}{phone}{form_type}'.encode()).hexdigest()}"
    try:
        already = await storage.redis.set(dedup_key, "1", ex=60, nx=True)
        if not already:
            return {"ok": True, "dedup": True}
    except Exception:
        pass

    try:
        async with db.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO requests (name, phone, child_age, type)
                VALUES ($1, $2, $3, $4)
            """, name, phone, child_age, form_type)
    except Exception:
        pass

    line = "\u2500" * 20
    text = (
        f"\U0001f99c <b>НОВА ЗАЯВКА</b> \U0001f99c\n"
        f"{line}\n\n"
        f"\U0001f4cb <b>Тип:</b> {form_type}\n"
        f"\U0001f464 <b>\u0406м\u2019я:</b> {name}\n"
        f"\U0001f4de <b>Телефон:</b> <code>{phone}</code>\n"
        f"\U0001f476 <b>В\u0456к дитини:</b> {child_age}\n\n"
        f"{line}\n"
        f"\u23f0 <i>Передзвон\u0456ть якнайшвидше!</i>"
    )

    # Відправляємо в KeyCRM
    if KEYCRM_API_KEY:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "pipeline_id": 1,
                    "status_id": 1,
                    "name": f"{form_type} - {name}",
                    "comment": f"Вік дитини: {child_age}",
                    "contact": {
                        "full_name": name,
                        "phone": phone,
                    }
                }
                async with session.post(
                    "https://openapi.keycrm.app/v1/leads",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {KEYCRM_API_KEY}",
                        "Content-Type": "application/json"
                    }
                ) as resp:
                    result = await resp.json()
                    logger.info(f"KeyCRM lead created: {result}")
        except Exception as e:
            logger.error(f"KeyCRM error: {e}")

    try:
        # Збираємо всіх адмінів без дублів
        async with db.pool.acquire() as conn:
            db_admins = await conn.fetch("SELECT id FROM users WHERE is_admin=TRUE")
        
        recipients = set([ADMIN_CHAT_ID])
        for a in db_admins:
            recipients.add(a["id"])
        
        logger.info(f"[NOTIFY] Sending to {len(recipients)} recipients: {recipients}")
        
        for chat_id in recipients:
            try:
                await bot.send_message(chat_id=chat_id, text=text)
            except Exception as e:
                logger.error(f"Failed to send to {chat_id}: {e}")
        
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"ok": False, "error": str(e)}

@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if token != WEBHOOK_SECRET:
        return {"ok": False}
    data = await request.json()
    update = types.Update(**data)
    await dp.feed_update(bot=bot, update=update)
    return {"ok": True}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
