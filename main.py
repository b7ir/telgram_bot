import os
import asyncio
import json
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ===== ADMIN =====
ADMIN_ID = 1621554170

# ===== نرخەکانی خاڵ =====
LIKE_PRICE_PER_100 = 10
FOLLOW_PRICE_PER_100 = 20
VIEW_PRICE_PER_100 = 5

pending_orders = {}

# ===== TOKEN =====
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

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
        users[uid] = {"points": 0}
        save_users(users)

    return users[uid]

def change_points(user_id, amount):
    users = load_users()
    uid = str(user_id)

    if uid not in users:
        users[uid] = {"points": 0}

    users[uid]["points"] += amount

    if users[uid]["points"] < 0:
        users[uid]["points"] = 0

    save_users(users)

# ===== KEYBOARDS =====
menu_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🛒 خزمەتگوزاریەکان", callback_data="services")],
        [InlineKeyboardButton(text="👤 هەژمار", callback_data="profile")]
    ]
)

services_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="👍 لایک", callback_data="like_service")],
        [InlineKeyboardButton(text="➕ فۆلۆو", callback_data="follow_service")],
        [InlineKeyboardButton(text="👀 بینین", callback_data="view_service")],
        [InlineKeyboardButton(text="🔙 گەڕانەوە", callback_data="back")]
    ]
)

# ===== START =====
@dp.message(Command("start"))
async def start(message: types.Message):
    get_user(message.from_user.id)
    await message.answer("👋 بەخێربێیت", reply_markup=menu_keyboard)

# ===== ADMIN ADD POINTS =====
@dp.message(Command("addpoints"))
async def add_points(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ تۆ ئەدمین نیت")
        return

    args = message.text