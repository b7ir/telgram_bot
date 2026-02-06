import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import time

user_last_start = {}
START_COOLDOWN = 5  # چرکە
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
    user_id = message.from_user.id
    now = time.time()

    if user_id in user_last_start:
        if now - user_last_start[user_id] < START_COOLDOWN:
            return  # هیچ وەڵامێک مەدە

    user_last_start[user_id] = now

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

    # ===== MAIN MENU =====
    if data == "services":
        await callback.message.edit_text(
            "🛒 خزمەتگوزاریەکان\n👇 هەڵبژێرە:",
            reply_markup=services_keyboard
        )

    elif data == "ads":
        await callback.message.answer("📣 ڕیکلامەکان")

    elif data == "upgrade":
        await callback.message.answer("✨ گۆڕانکاری")

    elif data == "transfer":
        await callback.message.answer("🔄 گواستنەوەی خاڵ")

    elif data == "redeem":
        await callback.message.answer("💳 بەکارهێنانی کۆد")

    elif data == "profile":
        user = callback.from_user
        await callback.message.answer(
            f"👤 زانیاری هەژمار\n\n"
            f"🆔 ID: `{user.id}`\n"
            f"👤 ناو: {user.full_name}\n"
            f"🔗 یوزەرنەیم: @{user.username if user.username else 'نییە'}",
            parse_mode="Markdown"
        )

    elif data == "support":
        await callback.message.answer("📬 پشتیوانی\n\n📩 پەیوەندی بکە: @YourSupport")

    elif data == "stats":
        await callback.message.answer("📊 ئامارەکان\n\n🚧 لە داهاتوودا")

    elif data == "help":
        await callback.message.answer("❓ یارمەتیدان\n\nℹ️ دووگمەکان بەکاربهێنە")

    # ===== SERVICES =====
    elif data == "like_service":
        await callback.message.answer("👍 خزمەتگوزاری لایک\n\n💰 نرخ: 1000 لایک = X$")

    elif data == "follow_service":
        await callback.message.answer("➕ خزمەتگوزاری فۆلۆو\n\n💰 نرخ: 1000 فۆلۆو = X$")

    elif data == "view_service":
        await callback.message.answer("👀 خزمەتگوزاری بینین\n\n💰 نرخ: 1000 بینین = X$")

    elif data == "back_to_main":
        await callback.message.edit_text(
            "👇 سەرەتا",
            reply_markup=menu_keyboard
        )

    await callback.answer()