import os
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

# ===== TOKEN =====
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== دوگمەکان (Menu) =====
menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="🛒 خەزمەتگوزاریەکان", callback_data="services")
    ],
    [
        InlineKeyboardButton(text="📢 گەشەپێدانی کەناڵەکان", callback_data="ads")
    ],
    [
        InlineKeyboardButton(text="✨ گوگڵەوە", callback_data="boost"),
        InlineKeyboardButton(text="🔄 گواستنەوەی خال", callback_data="transfer")
    ],
    [
        InlineKeyboardButton(text="💳 بەکارهێنانی کۆد", callback_data="redeem"),
        InlineKeyboardButton(text="👤 هەژمار", callback_data="account")
    ],
    [
        InlineKeyboardButton(text="📩 داواکاریەکان", callback_data="requests"),
        InlineKeyboardButton(text="📬 زانیاری داواکاری", callback_data="status")
    ],
    [
        InlineKeyboardButton(text="💰 کرینی خال", callback_data="buy")
    ],
    [
        InlineKeyboardButton(text="📊 ئامارەکان", callback_data="stats")
    ],
    [
        InlineKeyboardButton(text="📝 مراجعەکان", callback_data="refs")
    ],
    [
        InlineKeyboardButton(text="❓ پرسیار", callback_data="help")
    ]
])

# ===== /start =====
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 بەخێربێیت بۆ *Your Support*\n\n"
        "💰 خال: 0\n"
        "🆔 ناسنامەی تۆ: {}\n\n"
        "تکایە یەکێک لە دوگمەکان هەڵبژێرە 👇".format(message.from_user.id),
        parse_mode="Markdown",
        reply_markup=menu_keyboard
    )

# ===== Callback (یەک کۆد بۆ هەموو دوگمەکان) =====
@dp.callback_query()
async def menu_handler(callback: CallbackQuery):
    data = callback.data

    if data == "services":
        text = "🛒 *خەزمەتگوزاریەکان*\nئەم بەشە بۆ فرۆشتنەکانە."
    elif data == "ads":
        text = "📢 *گەشەپێدانی کەناڵەکان*"
    elif data == "boost":
        text = "✨ *گوگڵەوە / Boost*"
    elif data == "transfer":
        text = "🔄 *گواستنەوەی خال*"
    elif data == "redeem":
        text = "💳 *بەکارهێنانی کۆد*"
    elif data == "account":
        text = "👤 *هەژمارەکەت*"
    elif data == "requests":
        text = "📩 *داواکاریەکان*"
    elif data == "status":
        text = "📬 *زانیاری داواکاری*"
    elif data == "buy":
        text = "💰 *کرینی خال*"
    elif data == "stats":
        text = "📊 *ئامارەکان*"
    elif data == "refs":
        text = "📝 *مراجعەکان*"
    elif data == "help":
        text = "❓ *یارمەتی / پرسیار*"
    else:
        text = "❌ هەڵبژاردنێکی نادروست"

    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

# ===== MAIN =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())