import os
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ====== TOKEN ======
TOKEN = os.getenv("BOT_TOKEN")

# ====== BOT & DISPATCHER ======
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ====== /start ======
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 بەخێربێیت!\n\n"
        "🤖 بۆت بە سەربەخۆیی کار دەکات.\n"
        "ئێستا هیچ دوگمەیەک نییە، هەموو شتێک سەلامەتە ✅"
    )

# ====== MAIN ======
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())