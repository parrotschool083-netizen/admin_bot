from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Всі користувачі", callback_data="admin_users")],
        [InlineKeyboardButton(text="📋 Всі заявки", callback_data="admin_requests")],
        [InlineKeyboardButton(text="➕ Додати адміна", callback_data="admin_add")],
        [InlineKeyboardButton(text="📢 Розсилка", callback_data="admin_broadcast")],
    ])
