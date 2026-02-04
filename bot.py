import os
from aiogram import Bot, Dispatcher, executor, types

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("👋 بوت کار دەکات")

if __name__ == "__main__":
    executor.start_polling(dp)
