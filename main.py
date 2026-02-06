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
#===========
services_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="👍 لایک (Instagram / TikTok)", callback_data="like_service")],
        [InlineKeyboardButton(text="➕ فۆلۆو (Instagram / TikTok)", callback_data="follow_service")],
        [InlineKeyboardButton(text="👀 بینینی ڤیدیۆ", callback_data="view_service")],
        [InlineKeyboardButton(text="🔙 گەڕانەوە", callback_data="back_to_main")]
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
        await callback.message.edit_text(
            "🛒 خزمەتگوزاریەکان\n👇 هەڵبژێرە:",
            reply_markup=services_keyboard
        )

    elif data == "profile":
        user = callback.from_user
        await callback.message.answer(
            f"👤 زانیاری هەژمار\n\n"
            f"🆔 ID: `{user.id}`\n"
            f"👤 ناو: {user.full_name}\n"
            f"🔗 یوزەرنەیم: @{user.username if user.username else 'نییە'}",
            parse_mode="Markdown"
        )

    elif data == "back_to_main":
        await callback.message.edit_text(
            "👇 سەرەتا",
            reply_markup=menu_keyboard
        )

    elif data == "like_service":
        await callback.message.answer("👍 خزمەتگوزاری لایک")

    elif data == "follow_service":
        await callback.message.answer("➕ خزمەتگوزاری فۆلۆو")

    elif data == "view_service":
        await callback.message.answer("👀 خزمەتگوزاری بینین")

    await callback.answer()