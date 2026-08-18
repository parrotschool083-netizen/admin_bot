from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.client import main_menu, back_button
import db

router = Router()

class RequestForm(StatesGroup):
    name = State()
    phone = State()
    child_age = State()

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    async with db.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (id, username, full_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (id) DO UPDATE SET username=$2, full_name=$3
        """, message.from_user.id, message.from_user.username, message.from_user.full_name)

    await message.answer(
        "🦜 <b>Ласкаво просимо до Parrot School!</b>\n\n"
        "Ми — школа англійської мови для дітей 5–17 років у Харкові.\n"
        "Офіційний центр Cambridge Examinations.\n\n"
        "Оберіть що вас цікавить 👇",
        reply_markup=main_menu()
    )

@router.callback_query(F.data == "back_main")
async def back_to_main(call: CallbackQuery):
    await call.message.edit_text(
        "🦜 <b>Parrot School</b> — оберіть що вас цікавить 👇",
        reply_markup=main_menu()
    )

@router.callback_query(F.data == "info_prices")
async def info_prices(call: CallbackQuery):
    await call.message.edit_text(
        "💰 <b>Ціни та формати навчання</b>\n\n"
        "👥 <b>Групові</b> — від 1700₴/міс\n"
        "З підписанням оферти до кінця семестра\n"
        "✅ 8 занять на місяць\n"
        "✅ Розмовний клуб включено\n"
        "✅ Telegram бот для батьків\n"
        "✅ Підготовка до Cambridge\n\n"
        "👫 <b>Дуо</b> — 400₴/год\n"
        "Група на двох · Максимальна увага\n"
        "✅ 8 занять на місяць\n"
        "✅ Всі опції як у групових\n\n"
        "👤 <b>Індивідуально</b> — 600₴/год\n"
        "✅ Гнучкий розклад\n"
        "✅ Персональна програма\n"
        "✅ Cambridge прискорено\n\n"
        "🎁 <b>Перший урок — безкоштовно!</b>",
        reply_markup=back_button()
    )

@router.callback_query(F.data == "info_camp")
async def info_camp(call: CallbackQuery):
    await call.message.edit_text(
        "🏕️ <b>Parrot Camp — Літній табір 2026</b>\n\n"
        "Дитячий англомовний табір з повним зануренням у мову!\n\n"
        "📅 <b>Зміна 1:</b> 28.06 – 05.07\n"
        "📅 <b>Зміна 2:</b> 02.08 – 09.08\n\n"
        "✅ Повністю англомовне середовище\n"
        "✅ Квести, творчі майстерні, спорт\n"
        "✅ Нічне кіно та вечірні заходи\n"
        "✅ Нові друзі та пригоди\n\n"
        "10 днів — і рівень мови злетить! 🚀",
        reply_markup=back_button()
    )

@router.callback_query(F.data == "info_events")
async def info_events(call: CallbackQuery):
    await call.message.edit_text(
        "🎉 <b>Події та свята Parrot School</b>\n\n"
        "Тричі на рік ми збираємось усією сім'єю школи!\n\n"
        "🎃 <b>Halloween Party</b> — жовтень\n"
        "Костюми, аніматори, театральна вистава учнів англійською\n\n"
        "🎄 <b>Christmas & New Year Show</b> — грудень\n"
        "Новорічна вистава, Санта-Клаус, подарунки, дискотека\n\n"
        "🌷 <b>Spring Show</b> — квітень\n"
        "Театральна постановка: Шрек, Холодне серце, Мадагаскар...\n\n"
        "💬 <b>Speaking Clubs</b> — щотижня\n"
        "Розмовні клуби для всіх вікових груп. Безкоштовно!",
        reply_markup=back_button()
    )

@router.callback_query(F.data == "info_about")
async def info_about(call: CallbackQuery):
    await call.message.edit_text(
        "🏫 <b>Про Parrot School</b>\n\n"
        "🦜 Школа англійської для дітей 5–17 років\n"
        "📍 5 локацій у Харкові\n"
        "👨‍👩‍👧 300+ щасливих учнів\n"
        "🎓 Офіційний центр Cambridge Examinations\n"
        "⭐ 4 роки на ринку Харкова\n\n"
        "<b>Чому обирають нас:</b>\n"
        "✅ Викладачі — друзі та ментори\n"
        "✅ Система мотивації та нагород\n"
        "✅ Homework-Free Pass за успіхи\n"
        "✅ Щомісячний прогрес-звіт батькам\n"
        "✅ Cambridge сертифікати A1–C2\n\n"
        "🌐 Сайт: parrotschool.com.ua",
        reply_markup=back_button()
    )

@router.callback_query(F.data == "info_locations")
async def info_locations(call: CallbackQuery):
    await call.message.edit_text(
        "📍 <b>5 локацій Parrot School у Харкові</b>\n\n"
        "🟠 <b>м. Салтівська</b>\nвул. Нескорених, 26\n\n"
        "🟠 <b>м. Спортивна</b>\nвул. Тарасівська, 2а\n\n"
        "🟠 <b>м. Олексіївська</b>\nпр-кт Людвіга Свободи, 48Г\n\n"
        "🟠 <b>м. Холодна Гора</b>\nвул. Петра Балбочана, 54\n\n"
        "🟠 <b>м. Одеська</b>\nАерокосмічний пр-кт, 181/3\n\n"
        "Обирай найближчу до тебе! 🗺️",
        reply_markup=back_button()
    )

@router.callback_query(F.data == "info_teachers")
async def info_teachers(call: CallbackQuery):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👩‍🏫 Всі викладачі на сайті →", url="https://parrotschool083-netizen.github.io/parrotschool-website/pages/vykladachi.html")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")],
        [InlineKeyboardButton(text="📝 Залишити заявку", callback_data="leave_request")],
    ])
    await call.message.edit_text(
        "👩‍🏫 <b>Наші викладачі</b>\n\n"
        "🦜 <b>Леся</b> — викладач англійської\n"
        "<i>«Робота вчителем — це бачити, як "я не вмію" перетворюється на "у мене вийшло"»</i>\n\n"
        "🦜 <b>Вячеслава</b> — викладач англійської\n"
        "<i>«Люблю моменти, коли бачу щирий інтерес і маленькі перемоги учнів»</i>\n\n"
        "🦜 <b>Катя</b> — викладач англійської\n"
        "<i>«Подобається допомагати учням та бачити їхній прогрес»</i>\n\n"
        "🦜 <b>Оля</b> — викладач англійської\n"
        "<i>«Найголовніше — щоб учні не боялися зробити помилку»</i>\n\n"
        "🦜 <b>Вова</b> — викладач англійської\n"
        "<i>«Найголовніше — створити середовище для комфортного успіху»</i>\n\n"
        "Детальніше про кожного — на сайті 👇",
        reply_markup=kb
    )

@router.callback_query(F.data == "leave_request")
async def leave_request(call: CallbackQuery, state: FSMContext):
    await state.set_state(RequestForm.name)
    await call.message.edit_text(
        "📝 <b>Залишити заявку</b>\n\n"
        "Перший урок — безкоштовно!\n\n"
        "Як вас звати? 👇"
    )

@router.message(RequestForm.name)
async def request_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(RequestForm.phone)
    await message.answer("📞 Ваш номер телефону?")

@router.message(RequestForm.phone)
async def request_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(RequestForm.child_age)
    await message.answer("👶 Вік дитини?")

@router.message(RequestForm.child_age)
async def request_age(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    await state.clear()

    async with db.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO requests (user_id, name, phone, child_age, type)
            VALUES ($1, $2, $3, $4, $5)
        """, message.from_user.id, data['name'], data['phone'], message.text, 'Telegram заявка')

    admin_id = int(os.environ["ADMIN_CHAT_ID"])
    await bot.send_message(
        chat_id=admin_id,
        text=(
            f"🦜 <b>НОВА ЗАЯВКА — Parrot School</b>\n\n"
            f"📋 <b>Тип:</b> Telegram заявка\n"
            f"👤 <b>Ім'я:</b> {data['name']}\n"
            f"📞 <b>Телефон:</b> {data['phone']}\n"
            f"👶 <b>Вік дитини:</b> {message.text}\n"
            f"🆔 <b>Telegram:</b> @{message.from_user.username or 'немає'}"
        )
    )

    await message.answer(
        "✅ <b>Заявку прийнято!</b>\n\n"
        "🦜 Ми зателефонуємо вам найближчим часом.\n"
        "Дякуємо що обрали Parrot School!",
        reply_markup=main_menu()
    )

import os
