import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.enums.chat_type import ChatType
from aiogram import F
from aiogram.client.default import DefaultBotProperties

# ✅ Your Bot Token Here
BOT_TOKEN = "8024704510:AAHjxDzZRCeqrwkwDkqNO1PSudfcDUxyoWg"

# Win Stickers – Add more if you like (file_ids)
WIN_STICKERS = [
    "CAACAgUAAxkBAAEBIY1kZn1avRMZ6JtPXPmZ7tiJ0L8GRAACcQEAAladvQpQ3MSTp6BD6TUE",
    "CAACAgUAAxkBAAEBIY5kZn1aRY_MZMFov8Hrd7-2S5NmXwACXwEAAladvQoRjqL3Tx7kEzUE",
    "CAACAgUAAxkBAAEBIY9kZn1a1sn60n8G_UZDH1E4bybA_gACfgEAAladvQrbXZYoZ3pYjzUE"
]

# Bot + Dispatcher
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Fancy multiplier formatting
def fancy_multiplier(x):
    normal = "0123456789x."
    fancy = "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵𝘅․"
    return "".join(fancy[normal.index(c)] if c in normal else c for c in f"{x}x")

# Prediction Generator
def get_prediction():
    emojis = ["🔥", "✈️", "💨", "⚡", "🪂", "🌪️"]
    actions = ["Aviator Jump", "Aviator Boost", "Aviator Glide", "Aviator Fire", "Aviator Fly", "Aviator Turbo"]
    emoji = random.choice(emojis)
    action = random.choice(actions)
    multiplier = round(random.uniform(1.1, 5.0), 2)
    return f"{emoji} {action}\n{fancy_multiplier(multiplier)}"

# Prediction message sender
async def send_prediction(chat_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Pass", callback_data="pass"),
         InlineKeyboardButton(text="❌ Fail", callback_data="fail")]
    ])
    await bot.send_message(chat_id, get_prediction(), reply_markup=keyboard)

# /predict command to trigger first prediction (in channel)
@dp.message(F.chat.type == ChatType.CHANNEL, F.text == "/predict")
async def predict_cmd(message: types.Message):
    await send_prediction(message.chat.id)

# Callback for Pass / Fail
@dp.callback_query(F.data.in_({"pass", "fail"}))
async def handle_result(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    await callback.answer()
    
    if callback.data == "pass":
        sticker = random.choice(WIN_STICKERS)
        await bot.send_sticker(chat_id, sticker)
    
    # Send next prediction
    await send_prediction(chat_id)

# Start the bot
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
