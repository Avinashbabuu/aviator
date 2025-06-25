import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.enums.chat_type import ChatType
from aiogram import F
from aiogram.client.default import DefaultBotProperties

# ✅ Your Bot Token Here
BOT_TOKEN = "8024704510:AAFvyAZq7-Bg2FJDRr71PS5xd6hB81AvR6Y"

# Start with empty sticker list
WIN_STICKERS = []

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
    emojis = ["🔥", "✈️", "💨", "⚡", "𞥂", "🌪️"]
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

# Handle all messages that mention the bot in a channel
@dp.message(F.chat.type == ChatType.CHANNEL, F.entities)
async def handle_mention(message: types.Message):
    for entity in message.entities:
        if entity.type == "mention":
            mentioned_text = message.text[entity.offset:entity.offset + entity.length]
            if mentioned_text.lower() == f"@{(await bot.me()).username.lower()}":
                await send_prediction(message.chat.id)
                break

# Handle /predict in private chat (DM)
@dp.message(F.chat.type == ChatType.PRIVATE, F.text == "/predict")
async def handle_private_predict(message: types.Message):
    await send_prediction(message.chat.id)

# Handle /file to instruct user
@dp.message(F.chat.type == ChatType.PRIVATE, F.text == "/file")
async def handle_file_command(message: types.Message):
    await message.answer("📎 Send me any sticker, photo, or gif to use as WIN sticker when 'Pass' is clicked.")

# Save any sticker/photo/gif sent by user
@dp.message(F.chat.type == ChatType.PRIVATE, F.content_type.in_(["sticker", "photo", "animation"]))
async def save_file_id(message: types.Message):
    global WIN_STICKERS
    file_id = None

    if message.sticker:
        file_id = message.sticker.file_id
    elif message.photo:
        file_id = message.photo[-1].file_id
    elif message.animation:
        file_id = message.animation.file_id

    if file_id:
        WIN_STICKERS.append(file_id)
        await message.reply(f"✅ File saved!")
    else:
        await message.reply("❌ Unable to save file.")

# Callback for Pass / Fail
@dp.callback_query(F.data.in_({"pass", "fail"}))
async def handle_result(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    await callback.answer()

    if callback.data == "pass":
        if WIN_STICKERS:
            try:
                sticker = random.choice(WIN_STICKERS)
                await bot.send_sticker(chat_id, sticker)
            except Exception as e:
                print("⚠️ Failed to send sticker:", e)

    # Send next prediction
    await send_prediction(chat_id)

# Start the bot
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
