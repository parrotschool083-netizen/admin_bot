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

async def run_polling():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

@asynccontextmanager
async def lifespan(app: FastAPI):
    dp.include_router(client.router)
    dp.include_router(admin.router)
    await db.init_db()
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Головне меню"),
        types.BotCommand(command="admin", description="Адмін панель"),
    ])
    polling_task = asyncio.create_task(run_polling())
    logger.info("Bot started polling")
    yield
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        pass
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

    # Дедублікація через Redis — один і той самий запит не надсилаємо двічі
    dedup_key = f"form:{hashlib.md5(f'{name}{phone}{child_age}{form_type}'.encode()).hexdigest()}"
    already = await storage.redis.set(dedup_key, "1", ex=60, nx=True)
    if not already:
        return {"ok": True, "dedup": True}

    try:
        async with db.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO requests (name, phone, child_age, type)
                VALUES ($1, $2, $3, $4)
            """, name, phone, child_age, form_type)
    except Exception:
        pass

    text = (
        "\U0001f99c <b>НОВА ЗАЯВКА</b> \U0001f99c\n"
        "\u2500" * 28 + "\n\n"
        f"\U0001f4cb <b>Тип:</b>  {form_type}\n"
        f"\U0001f464 <b>Ім\u2019я:</b>  {name}\n"
        f"\U0001f4de <b>Телефон:</b>  <code>{phone}</code>\n"
        f"\U0001f476 <b>Вік дитини:</b>  {child_age}\n\n"
        "\u2500" * 28 + "\n"
        "\u23f0 <i>Передзвоніть якнайшвидше!</i>"
    )

    # Відправляємо в KeyCRM
    if KEYCRM_API_KEY:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "pipeline_id": 1,
                    "source_id": 1,
                    "buyer": {
                        "full_name": name,
                        "phone": phone,
                    },
                    "fields": [
                        {"name": "Вік дитини", "value": child_age},
                        {"name": "Тип заявки", "value": form_type},
                    ]
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
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)
        async with db.pool.acquire() as conn:
            admins = await conn.fetch("SELECT id FROM users WHERE is_admin=TRUE AND id!=$1", ADMIN_CHAT_ID)
        for a in admins:
            try:
                await bot.send_message(chat_id=a["id"], text=text)
            except Exception:
                pass
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"ok": False, "error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
