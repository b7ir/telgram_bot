import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ===== TOKEN =====
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== MENU KEYBOARD =====
menu_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🛒 خزمەتگوزاریەکان", callback_data="services"),
        ],
        [
            InlineKeyboardButton(text="📢 کەشەپێدانی کەناڵەکان", callback_data="ads"),
        ],
        [
            InlineKeyboardButton(text="✨ گۆڕانکاری", callback_data="upgrade"),
            InlineKeyboardButton(text="🔄 گواستنەوەی خال", callback_data="transfer"),
        ],
        [
            InlineKeyboardButton(text="💳 بەکارهێنانی کۆد", callback_data="redeem"),
            InlineKeyboardButton(text="👤 هەژمار", callback_data="profile"),
        ],
        [
            InlineKeyboardButton(text="📬 زانیاری داواکاری", callback_data="support"),
            InlineKeyboardButton(text="📊 ئامارەکان", callback_data="stats"),
        ],
        [
            InlineKeyboardButton(text="❓ ڕێنمایی", callback_data="help"),
        ],
    ]
)

# ===== /start =====
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 بەخێربێیت!\n\n"
        "🤖 بۆت بە سەرکەوتوویی کار دەکات.\n"
        "👇 تکایە دووگمەیەک هەڵبژێرە:",
        reply_markup=menu_keyboard
    )

# ===== MAIN =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    @dp.callback_query()
async def handle_buttons(callback: types.CallbackQuery):
    data = callback.data
