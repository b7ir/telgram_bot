
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ====== دوگمەکانی مینو ======
menu_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 لیستی یەکەم", callback_data="menu_1"),
            InlineKeyboardButton(text="⚙️ لیستی دووەم", callback_data="menu_2")
        ],
        [
            InlineKeyboardButton(text="ℹ️ دەربارەی بوت", callback_data="about")
        ]
    ]
)

# ====== فەرمانی /start ======
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 بەخێربێیت!\nتکایە یەکێک لە لیستەکان هەڵبژێرە 👇",
        reply_markup=menu_keyboard
    )

# ====== وەڵامی دوگمەکان ======
@dp.callback_query(lambda c: c.data == "menu_1")
async def menu1(callback: types.CallbackQuery):
    await callback.message.answer("📋 ئەمە لیستی یەکەمە")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "menu_2")
async def menu2(callback: types.CallbackQuery):
    await callback.message.answer("⚙️ ئەمە لیستی دووەمە")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "about")
async def about(callback: types.CallbackQuery):
    await callback.message.answer("🤖 ئەم بوتە بە aiogram دروست کراوە")
    await callback.answer()

sale_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📱 مۆبایل - 300$", callback_data="sell_mobile"),
            InlineKeyboardButton(text="💻 لابتۆپ - 700$", callback_data="sell_laptop")
        ],
        [
            InlineKeyboardButton(text="🎧 هێدفۆن - 50$", callback_data="sell_headphone"),
            InlineKeyboardButton(text="⌚ کاتژمێر - 120$", callback_data="sell_watch")
        ],
        [
            InlineKeyboardButton(text="📞 پەیوەندی بە فرۆشیار", callback_data="contact"),
            InlineKeyboardButton(text="🔙 گەڕانەوە", callback_data="back_to_main")
        ]
    ]
)
menu_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🛒 خزمەتگوزاریەکان", callback_data="services"),
            InlineKeyboardButton(text="📢 کەشەی پێدان", callback_data="offers")
        ],
        [
            InlineKeyboardButton(text="ℹ️ دەربارەی بۆت", callback_data="about")
        ]
    ]
)
@dp.callback_query(lambda c: c.data == "services")
async def services_handler(callback: CallbackQuery):
    await callback.message.answer(
        "🛒 **لیستی خزمەتگوزاریەکان**:\n\n"
        "1️⃣ فۆڵۆوەران\n"
        "2️⃣ لایک\n"
        "3️⃣ بینین\n\n"
        "تکایە یەکێک هەڵبژێرە 👇"
    )
    await callback.answer()
    