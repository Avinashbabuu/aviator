import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.enums.chat_type import ChatType
from aiogram import F
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = "8024704510:AAFvyAZq7-Bg2FJDRr71PS5xd6hB81AvR6Y"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Memory
WIN_STICKERS = []
CHANNEL_ID = None  # will be set via /setchannel

# Fancy multiplier
def fancy_multiplier(x):
    normal = "0123456789x."
    fancy = "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵𝘅․"
    return "".join(fancy[normal.index(c)] if c in normal else c for c in f"{x}x")

# Prediction text
def get_prediction():
    emojis = ["🔥", "✈️", "💨", "⚡", "𞥂", "🌪️"]
    actions = ["Aviator Spribe"]
    emoji = random.choice(emojis)
    action = random.choice(actions)
    multiplier = round(random.uniform(1.1, 5.0), 2)
    
    prediction_line = f"{emoji} <b>{action}</b>\n<b>{fancy_multiplier(multiplier)}</b>"

    footer = (
        "\n\n<blockquote>🎮 <b>Play at your own risk</b></blockquote>\n"
        "🛡️ <blockquote>Maintain <b>Level 1 to 3</b></blockquote>\n"
        "🔗 <b><blockquote>Register with our official link</b>, otherwise <b>hack will not work</b>.</blockquote>\n"
        "<a href='https://bdgslotclub.com/#/register?inviteCode=46377313830'>🚀 Click here to Register</a>"
    )

    return prediction_line + footer


# Send prediction with buttons
async def send_prediction(chat_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Pass", callback_data="pass"),
         InlineKeyboardButton(text="❌ Fail", callback_data="fail")]
    ])
    await bot.send_message(chat_id, get_prediction(), reply_markup=keyboard)

# Mention in channel triggers prediction
@dp.message(F.chat.type == ChatType.CHANNEL, F.entities)
async def handle_mention(message: types.Message):
    for entity in message.entities:
        if entity.type == "mention":
            mentioned_text = message.text[entity.offset:entity.offset + entity.length]
            if mentioned_text.lower() == f"@{(await bot.me()).username.lower()}":
                await send_prediction(message.chat.id)
                break

# /predict in DM
@dp.message(F.chat.type == ChatType.PRIVATE, F.text == "/predict")
async def handle_private_predict(message: types.Message):
    await send_prediction(message.chat.id)

# /file command to instruct
@dp.message(F.chat.type == ChatType.PRIVATE, F.text == "/file")
async def handle_file_command(message: types.Message):
    await message.answer("📎 Send me any sticker, photo, or gif to use as WIN sticker when 'Pass' is clicked.")

# Save sticker/gif
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

# Handle Pass / Fail button clicks
@dp.callback_query(F.data.in_({"pass", "fail"}))
async def handle_result(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    await callback.answer()
    if callback.data == "pass" and WIN_STICKERS:
        try:
            sticker = random.choice(WIN_STICKERS)
            await bot.send_sticker(chat_id, sticker)
        except Exception as e:
            print("⚠️ Failed to send sticker:", e)
    await send_prediction(chat_id)

# Inline query support (@botname get)
@dp.inline_query()
async def inline_query_handler(inline_query: types.InlineQuery):
    input_text = inline_query.query.lower()
    if "get" in input_text or input_text == "":
        prediction = get_prediction()
        result = types.InlineQueryResultArticle(
            id="1",
            title="🎯 Get Aviator Prediction",
            input_message_content=types.InputTextMessageContent(message_text=prediction),
            description="Click to get prediction",
            thumb_url="https://ossimg.bdg123456.com/BDGWin/gamelogo/SPRIBE/22001.png"
        )
        await bot.answer_inline_query(inline_query.id, results=[result], cache_time=1)

# ✅ /setchannel — Set the channel ID manually from DM
@dp.message(F.chat.type == ChatType.PRIVATE, F.text == "/setchannel")
async def set_channel(message: types.Message):
    global CHANNEL_ID
    await message.reply("📣 Send me your channel @username or numeric ID")
    dp.message.register(awaiting_channel_input)

async def awaiting_channel_input(message: types.Message):
    global CHANNEL_ID
    CHANNEL_ID = message.text.strip()
    await message.answer(f"✅ Channel set to: <code>{CHANNEL_ID}</code>")

# ✅ /sendpredict — Send prediction to saved channel
@dp.message(F.chat.type == ChatType.PRIVATE, F.text == "/sendpredict")
async def send_prediction_to_channel(message: types.Message):
    if not CHANNEL_ID:
        await message.reply("❌ Channel not set. Use /setchannel first.")
        return
    try:
        await send_prediction(CHANNEL_ID)
        await message.reply("✅ Prediction sent to channel.")
    except Exception as e:
        await message.reply(f"❌ Failed: {e}")

# Start polling
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
