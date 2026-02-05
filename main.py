import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ====== MENU BUTTONS ======
menu_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Menu 1", callback_data="menu_1"),
            InlineKeyboardButton(text="⚙️ Menu 2", callback_data="menu_2")
        ],
        [
            InlineKeyboardButton(text="ℹ️ About", callback_data="about")
        ]
    ]
)

# ====== /start COMMAND ======
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 Welcome!\nChoose from the menu below:",
        reply_markup=menu_keyboard
    )

# ====== BUTTON HANDLERS ======
@dp.callback_query(lambda c: c.data == "menu_1")
async def menu1(callback: types.CallbackQuery):
    await callback.message.answer("📋 You clicked Menu 1")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "menu_2")
async def menu2(callback: types.CallbackQuery):
    await callback.message.answer("⚙️ You clicked Menu 2")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "about")
async def about(callback: types.CallbackQuery):
    await callback.message.answer("🤖 This is a Telegram bot built with aiogram")
    await callback.answer()

# ====== RUN BOT ======
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())