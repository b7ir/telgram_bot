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

# ====== کارپێکردنی بوت ======
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())