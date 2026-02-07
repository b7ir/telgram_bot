import os
import asyncio
import time
import json
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

user_last_start = {}
START_COOLDOWN = 5  # چرکە
# ===== TOKEN =====
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

# ===== BOT & DISPATCHER =====
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== POINTS SYSTEM =====
DATA_FILE = Path("users.json")

def load_users():
    if not DATA_FILE.exists():
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(user_id):
    users = load_users()
    uid = str(user_id)

    if uid not in users:
        users[uid] = {
            "points": 0
        }
        save_users(users)

    return users[uid]
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
    # 👇 دڵنیابوون لە تۆمارکردنی بەکارهێنەر
    get_user(message.from_user.id)

    await message.answer(
        "👋 بەخێربێیت!\n"
        "🤖 بۆت بە سەرکەوتوویی کار دەکات.\n"
        "👇 دووگمەی خوارەوە بەکاربهێنە:",
        reply_markup=menu_keyboard
    )
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
    # ===== MAIN =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())