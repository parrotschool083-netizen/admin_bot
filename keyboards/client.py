from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Ціни та формати", callback_data="info_prices")],
        [InlineKeyboardButton(text="🏕️ Parrot Camp", callback_data="info_camp")],
        [InlineKeyboardButton(text="🎉 Події та свята", callback_data="info_events")],
        [InlineKeyboardButton(text="🏫 Про школу", callback_data="info_about")],
        [InlineKeyboardButton(text="📍 Локації", callback_data="info_locations")],
        [InlineKeyboardButton(text="👩‍🏫 Викладачі", callback_data="info_teachers")],
        [InlineKeyboardButton(text="📝 Залишити заявку", callback_data="leave_request")],
    ])

def back_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")],
        [InlineKeyboardButton(text="📝 Залишити заявку", callback_data="leave_request")],
    ])
