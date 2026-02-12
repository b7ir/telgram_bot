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

    args = message.text.split()

    if len(args) != 3:
        await message.answer("❌ شێواز: /addpoints USER_ID AMOUNT")
        return

    try:
        user_id = int(args[1])
        amount = int(args[2])
    except ValueError:
        await message.answer("❌ ژمارە دروست نییە")
        return

    change_points(user_id, amount)

    await message.answer(
        f"✅ {amount} خاڵ زیاد کرا بۆ\n"
        f"🆔 {user_id}\n"
        f"💎 خاڵی نوێ: {get_user(user_id)['points']}"
    )

# ===== HANDLE SERVICE QUANTITY =====
@dp.message()
async def handle_quantity(message: types.Message):
    user_id = message.from_user.id

    if user_id not in pending_orders:
        return

    if not message.text.isdigit():
        await message.answer("تکایە تەنیا ژمارە بنووسە")
        return

    amount_100 = int(message.text)
    service = pending_orders[user_id]
    user_data = get_user(user_id)

    if service == "like":
        price = LIKE_PRICE_PER_100
        service_name = "لایک"
    elif service == "follow":
        price = FOLLOW_PRICE_PER_100
        service_name = "فۆلۆو"
    elif service == "view":
        price = VIEW_PRICE_PER_100
        service_name = "بینین"
    else:
        return

    total_cost = amount_100 * price

    if user_data["points"] < total_cost:
        await message.answer("❌ خاڵت بەس نییە")
        pending_orders.pop(user_id)
        return

    change_points(user_id, -total_cost)

    await message.answer(
        f"✅ داواکاری سەرکەوتوو بوو\n"
        f"📦 {amount_100 * 100} {service_name}\n"
        f"💎 {total_cost} خاڵ کەم کرا\n"
        f"💰 خاڵی ماوە: {get_user(user_id)['points']}"
    )

    pending_orders.pop(user_id)

# ===== CALLBACK BUTTONS =====
@dp.callback_query()
async def handle_buttons(callback: types.CallbackQuery):
    data = callback.data
    user = callback.from_user
    user_data = get_user(user.id)

    if data == "services":
        await callback.message.edit_text(
            "🛒 خزمەتگوزاریەکان",
            reply_markup=services_keyboard
        )

    elif data == "profile":
        await callback.message.answer(
            f"👤 هەژمار\n💎 خاڵ: {user_data['points']}"
        )

    elif data == "like_service":
        pending_orders[user.id] = "like"
        await callback.message.answer("چەند 100 لایک دەتەوێت؟\nنموونە: 3")

    elif data == "follow_service":
        pending_orders[user.id] = "follow"
        await callback.message.answer("چەند 100 فۆلۆو دەتەوێت؟\nنموونە: 2")

    elif data == "view_service":
        pending_orders[user.id] = "view"
        await callback.message.answer("چەند 100 بینین دەتەوێت؟\nنموونە: 5")

    elif data == "back":
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