from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.admin import admin_menu
import db
import os

router = Router()
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", 0))

async def is_admin(user_id: int) -> bool:
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT is_admin FROM users WHERE id=$1", user_id)
        if row and row['is_admin']:
            return True
    return user_id == ADMIN_CHAT_ID

class BroadcastState(StatesGroup):
    text = State()

class AddAdminState(StatesGroup):
    user_id = State()

@router.message(F.text == "/admin")
async def cmd_admin(message: Message):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Немає доступу")
        return
    await message.answer(
        "🦜 <b>Адмін панель Parrot School</b>\n\n"
        "Оберіть дію 👇",
        reply_markup=admin_menu()
    )

@router.callback_query(F.data == "admin_users")
async def admin_users(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    async with db.pool.acquire() as conn:
        users = await conn.fetch("SELECT * FROM users ORDER BY created_at DESC LIMIT 20")
    text = "👥 <b>Користувачі (останні 20):</b>\n\n"
    for u in users:
        text += f"{'👑' if u['is_admin'] else '👤'} {u['full_name']} (@{u['username']}) — <code>{u['id']}</code>\n"
    await call.message.edit_text(text, reply_markup=admin_menu())

@router.callback_query(F.data == "admin_requests")
async def admin_requests(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    async with db.pool.acquire() as conn:
        reqs = await conn.fetch("SELECT * FROM requests ORDER BY created_at DESC LIMIT 10")
    text = "📋 <b>Останні заявки:</b>\n\n"
    for r in reqs:
        text += (
            f"📝 <b>{r['type']}</b>\n"
            f"👤 {r['name']} | 📞 {r['phone']} | 👶 {r['child_age']}\n"
            f"🕐 {r['created_at'].strftime('%d.%m %H:%M')}\n\n"
        )
    await call.message.edit_text(text or "Заявок немає", reply_markup=admin_menu())

@router.callback_query(F.data == "admin_add")
async def admin_add(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await state.set_state(AddAdminState.user_id)
    await call.message.edit_text("➕ Введіть Telegram ID нового адміна:")

@router.message(AddAdminState.user_id)
async def admin_add_id(message: Message, state: FSMContext):
    try:
        new_id = int(message.text.strip())
        async with db.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET is_admin=TRUE WHERE id=$1", new_id
            )
        await state.clear()
        await message.answer(f"✅ Адміна <code>{new_id}</code> додано!", reply_markup=admin_menu())
    except ValueError:
        await message.answer("❌ Невірний ID. Введіть число:")

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await state.set_state(BroadcastState.text)
    await call.message.edit_text("📢 Введіть текст розсилки:")

@router.message(BroadcastState.text)
async def admin_broadcast_send(message: Message, state: FSMContext, bot):
    await state.clear()
    async with db.pool.acquire() as conn:
        users = await conn.fetch("SELECT id FROM users")
    ok = 0
    fail = 0
    for u in users:
        try:
            await bot.send_message(u['id'], f"📢 <b>Parrot School:</b>\n\n{message.text}")
            ok += 1
        except Exception:
            fail += 1
    await message.answer(
        f"✅ Розсилку завершено!\n\n"
        f"📨 Відправлено: {ok}\n"
        f"❌ Помилок: {fail}",
        reply_markup=admin_menu()
    )
