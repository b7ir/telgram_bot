import os
import asyncio
import json
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
# ===== نرخەکانی خاڵ =====
LIKE_COST = 10
FOLLOW_COST = 20
VIEW_COST = 5
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
def change_points(user_id, amount):
    users = load_users()
    uid = str(user_id)

    if uid not in users:
        users[uid] = {"points": 0}

    users[uid]["points"] += amount

    if users[uid]["points"] < 0:
        users[uid]["points"] = 0

    save_users(users)
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
    get_user(message.from_user.id)

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
elif data == "like_service":
    user = callback.from_user
    user_data = get_user(user.id)

    if user_data["points"] < LIKE_COST:
        await callback.message.answer("❌ خاڵت بەس نییە بۆ لایک")
    else:
        change_points(user.id, -LIKE_COST)
        await callback.message.answer(
            f"✅ لایک سەرکەوتوو بوو\n"
            f"💎 {LIKE_COST} خاڵ کەم کرا\n"
            f"💰 خاڵی ماوە: {get_user(user.id)['points']}"
        )
        elif data == "follow_service":
    user = callback.from_user
    user_data = get_user(user.id)

    if user_data["points"] < FOLLOW_COST:
        await callback.message.answer("❌ خاڵت بەس نییە بۆ فۆلۆو")
    else:
        change_points(user.id, -FOLLOW_COST)
        await callback.message.answer(
            f"✅ فۆلۆو سەرکەوتوو بوو\n"
            f"💎 {FOLLOW_COST} خاڵ کەم کرا\n"
            f"💰 خاڵی ماوە: {get_user(user.id)['points']}"
        )
        elif data == "view_service":
    user = callback.from_user
    user_data = get_user(user.id)

    if user_data["points"] < VIEW_COST:
        await callback.message.answer("❌ خاڵت بەس نییە بۆ بینین")
    else:
        change_points(user.id, -VIEW_COST)
        await callback.message.answer(
            f"✅ بینین سەرکەوتوو بوو\n"
            f"💎 {VIEW_COST} خاڵ کەم کرا\n"
            f"💰 خاڵی ماوە: {get_user(user.id)['points']}"
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
        user_data = get_user(user.id)

        await callback.message.answer(
            f"👤 هەژمار\n\n"
            f"🆔 ID: `{user.id}`\n"
            f"💎 خاڵ: {user_data['points']}\n"
            f"👤 ناو: {user.full_name}",
            parse_mode="Markdown"
        )

    elif data == "support":
        await callback.message.answer("📬 پشتیوانی")

    elif data == "stats":
        await callback.message.answer("📊 ئامارەکان")

    elif data == "help":
        await callback.message.answer("❓ یارمەتیدان")

    # ===== SERVICES =====
    elif data == "like_service":
        await callback.message.answer("👍 خزمەتگوزاری لایک")

    elif data == "follow_service":
        await callback.message.answer("➕ خزمەتگوزاری فۆلۆو")

    elif data == "view_service":
        await callback.message.answer("👀 خزمەتگوزاری بینین")

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