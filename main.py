import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")

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

    if data == "services":
        await callback.message.answer("🛒 خزمەتگوزاریەکان")
    elif data == "ads":
        await callback.message.answer("📣 ڕیکلامەکان")
    elif data == "upgrade":
        await callback.message.answer("✨ گۆڕانکاری")
    elif data == "transfer":
        await callback.message.answer("🔄 گواستنەوەی خاڵ")
    elif data == "redeem":
        await callback.message.answer("💳 بەکارهێنانی کۆد")
    elif data == "profile":
        await callback.message.answer("👤 هەژمار")
    elif data == "support":
        await callback.message.answer("📬 پشتیوانی")
    elif data == "stats":
        await callback.message.answer("📊 ئامارەکان")
    elif data == "help":
        await callback.message.answer("❓ یارمەتیدان")

    await callback.answer()

# ===== MAIN =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())