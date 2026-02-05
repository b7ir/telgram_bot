import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ===== TOKEN =====
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

# ===== BOT & DISPATCHER =====
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== MENU KEYBOARD =====
menu_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🛒 خزمەتگوزاریەکان", callback_data="services")],
        [InlineKeyboardButton(text="📣 ڕیکلامەکان", callback_data="ads")],
        [
            InlineKeyboardButton(text="✨ گۆڕانکاری", callback_data="upgrade"),
            InlineKeyboardButton(text="🔄 گواستنەوەی خاڵ", callback_data="transfer")
        ],
        [
            InlineKeyboardButton(text="💳 بەکارهێنانی کۆد", callback_data="redeem"),
            InlineKeyboardButton(text="👤 هەژمار", callback_data="profile")
        ],
        [
            InlineKeyboardButton(text="📬 پشتیوانی", callback_data="support"),
            InlineKeyboardButton(text="📊 ئامارەکان", callback_data="stats")
        ],
        [InlineKeyboardButton(text="❓ یارمەتیدان", callback_data="help")]
    ]
)

# ===== /start =====
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 بەخێربێیت!\n"
        "🤖 بۆت بە سەرکەوتوویی کار دەکات.\n"
        "👇 دووگمەی خوارەوە بەکاربهێنە:",
        reply_markup=menu_keyboard
    )

# ===== CALLBACK HANDLER =====
@dp.callback_query()
async def handle_buttons(callback: types.CallbackQuery):
    data = callback.data

    responses = {
        "services": "🛒 خزمەتگوزاریەکان",
        "ads": "📣 ڕیکلامەکان",
        "upgrade": "✨ گۆڕانکاری",
        "transfer": "🔄 گواستنەوەی خاڵ",
        "redeem": "💳 بەکارهێنانی کۆد",
        "profile": "👤 هەژمار",
        "support": "📬 پشتیوانی",
        "stats": "📊 ئامارەکان",
        "help": "❓ یارمەتیدان"
    }

    if data in responses:
        await callback.message.answer(responses[data])

    await callback.answer()

# ===== MAIN =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())