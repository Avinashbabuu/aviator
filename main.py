import asyncio
import random
import time
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.enums.chat_type import ChatType
from aiogram import F
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = "8024704510:AAFnYm2FAF_MKNQQcRIgxELTPc6QRvcREd4"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Memory storage
WIN_STICKERS = []
CHANNEL_ID = None
LAST_MULTIPLIER = {}  # chat_id: last multiplier
USER_COOLDOWNS = {}
CLICK_COOLDOWN_SECONDS = 10

# Fancy multiplier converter
def fancy_multiplier(x):
    normal = "0123456789x."
    fancy = "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵𝘅․"
    return "".join(fancy[normal.index(c)] if c in normal else c for c in f"{x}x")

# Prediction generator
def get_prediction():
    emojis = ["🔥", "✈️", "💨", "⚡", "𞥂", "🌪️"]
    actions = ["Aviator Spribe"]
    emoji = random.choice(emojis)
    action = random.choice(actions)
    multiplier = round(random.uniform(1.1, 5.0), 2)

    prediction_line = f"{emoji} <b>{action}</b>\n<b>{fancy_multiplier(multiplier)}</b>"

    footer = (
        "\n\n<blockquote>🎮 Play at your own risk</blockquote>"
        "<blockquote>🛡️ Maintain Level 1 to 3</blockquote>"
        "<blockquote>🔗 Register with our official link, otherwise hack will not work.</blockquote>\n"
        "<a href='https://bdgslotclub.com/#/register?inviteCode=46377313830'>🚀 Click here to Register</a>"
    )

    return prediction_line + footer, multiplier

# Send prediction and store multiplier
async def send_prediction(chat_id):
    global LAST_MULTIPLIER
    prediction_text, multiplier = get_prediction()
    LAST_MULTIPLIER[chat_id] = multiplier  # Store multiplier for delay use

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Profit", callback_data="pass"),
         InlineKeyboardButton(text="❌ Crash", callback_data="fail")]
    ])
    await bot.send_message(chat_id, prediction_text, reply_markup=keyboard)

# Mention-based prediction in channel
@dp.message(F.chat.type == ChatType.CHANNEL, F.entities)
async def handle_mention(message: types.Message):
    for entity in message.entities:
        if entity.type == "mention":
            mentioned_text = message.text[entity.offset:entity.offset + entity.length]
            if mentioned_text.lower() == f"@{(await bot.me()).username.lower()}":
                await send_prediction(message.chat.id)
                break

# /predict in private
@dp.message(F.chat.type == ChatType.PRIVATE, F.text == "/predict")
async def handle_private_predict(message: types.Message):
    await send_prediction(message.chat.id)

# /file command in DM
@dp.message(F.chat.type == ChatType.PRIVATE, F.text == "/file")
async def handle_file_command(message: types.Message):
    await message.answer("📎 Send me any sticker, photo, or gif to use as WIN sticker when 'Pass' is clicked.")

# Save WIN sticker/gif/photo
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
        await message.reply("✅ File saved!")
    else:
        await message.reply("❌ Unable to save file.")

# Handle button click (Pass/Fail)
@dp.callback_query(F.data.in_({"pass", "fail"}))
async def handle_result(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    current_time = time.time()

    # User spam protection
    if user_id in USER_COOLDOWNS and current_time - USER_COOLDOWNS[user_id] < CLICK_COOLDOWN_SECONDS:
        await callback.answer("🕒 Please wait before clicking again.", show_alert=True)
        return

    USER_COOLDOWNS[user_id] = current_time
    await callback.answer()

    # If PASS, send win sticker
    if callback.data == "pass" and WIN_STICKERS:
        try:
            sticker = random.choice(WIN_STICKERS)
            await bot.send_sticker(chat_id, sticker)
        except Exception as e:
            print("⚠️ Failed to send sticker:", e)

    # Delay logic
    multiplier = LAST_MULTIPLIER.get(chat_id, 2.0)
    delay_seconds = int(multiplier * 30) if callback.data == "pass" else 10

    await bot.send_message(chat_id, f"⏳ Next prediction in {delay_seconds} seconds...")
    await asyncio.sleep(delay_seconds)

    await send_prediction(chat_id)

# Inline query support
@dp.inline_query()
async def inline_query_handler(inline_query: types.InlineQuery):
    input_text = inline_query.query.lower()
    if "get" in input_text or input_text == "":
        prediction, _ = get_prediction()
        result = types.InlineQueryResultArticle(
            id="1",
            title="🎯 Get Aviator Prediction",
            input_message_content=types.InputTextMessageContent(message_text=prediction),
            description="Click to get prediction",
            thumb_url="https://ossimg.bdg123456.com/BDGWin/gamelogo/SPRIBE/22001.png"
        )
        await bot.answer_inline_query(inline_query.id, results=[result], cache_time=1)

# Set channel command
@dp.message(F.chat.type == ChatType.PRIVATE, F.text == "/setchannel")
async def set_channel(message: types.Message):
    global CHANNEL_ID
    await message.reply("📣 Send me your channel @username or numeric ID")
    dp.message.register(awaiting_channel_input)

async def awaiting_channel_input(message: types.Message):
    global CHANNEL_ID
    CHANNEL_ID = message.text.strip()
    await message.answer(f"✅ Channel set to: <code>{CHANNEL_ID}</code>")

# Send prediction to saved channel
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

# Start polling bot
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
