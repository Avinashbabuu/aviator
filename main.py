import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.enums.chat_type import ChatType
from aiogram import F
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = "8024704510:AAEAHW8NOFD0fSGnKyZB9notkOvF-2a2ORU"
ADMIN_ID = 6484788124  # Replace with your Telegram numeric ID

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

WIN_STICKERS = []
LAST_MULTIPLIER = {}
CRASH_MULTIPLIER = {}
prediction_task = None
is_running = False
CHANNEL_ID = None
CHANNEL_COUNTER = 0
MAX_CHANNEL_PREDICTIONS = 15
CUSTOM_MESSAGE = None
CUSTOM_MESSAGE_TYPE = None
CUSTOM_MESSAGE_CONTENT = None

# Fancy multiplier formatter
def fancy_multiplier(x):
    normal = "0123456789x."
    fancy = "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵𝘅․"
    return "".join(fancy[normal.index(c)] if c in normal else c for c in f"{x}x")

# Timing logic
def calculate_delay(multiplier):
    if multiplier <= 1.00:
        return 0
    return int(((multiplier - 1.00) / 0.11) * 3)

# Prediction + crash logic
def get_prediction():
    emojis = ["🔥", "✈️", "💨", "⚡", "𞥂", "🌪️"]
    emoji = random.choice(emojis)
    multiplier = round(random.uniform(1.00, 5.00), 2)
    crash = round(random.uniform(1.01, multiplier), 2)

    text = f"{emoji} <b>Aviator Spribe</b>\n<b>{fancy_multiplier(multiplier)}</b>"
    footer = ("\n\n<blockquote>🎮 Play at your own risk</blockquote>"
              "<blockquote>🛡️ Maintain Level 1 to 3</blockquote>"
              "<blockquote>🔗 Register with our official link, otherwise hack will not work.</blockquote>\n"
              "<a href='https://bdgslotclub.com/#/register?inviteCode=46377313830'>🚀 Click here to Register</a>")

    return text + footer, multiplier, crash

# Send prediction
async def send_prediction(chat_id):
    prediction_text, multiplier, crash = get_prediction()
    LAST_MULTIPLIER[chat_id] = multiplier
    CRASH_MULTIPLIER[chat_id] = crash

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Pass", callback_data="pass"),
            InlineKeyboardButton(text="❌ Crash", callback_data="fail")
        ],
        [
            InlineKeyboardButton(
                text="🚀 Register Now & Get ₹500 Bonus",
                url="https://bdgslotclub.com/#/register?inviteCode=46377313830"
            )
        ]
    ])
    await bot.send_message(chat_id, prediction_text, reply_markup=keyboard)

# Manual loop (for admin personal)
async def prediction_loop(chat_id):
    global is_running
    is_running = True
    while is_running:
        await send_prediction(chat_id)
        delay = calculate_delay(LAST_MULTIPLIER.get(chat_id, 2.0))
        await asyncio.sleep(delay)

# Channel loop with break
async def channel_prediction_loop():
    global CHANNEL_COUNTER
    while True:
        if CHANNEL_ID:
            for _ in range(MAX_CHANNEL_PREDICTIONS):
                await send_prediction(CHANNEL_ID)
                CHANNEL_COUNTER += 1
                await asyncio.sleep(calculate_delay(LAST_MULTIPLIER.get(CHANNEL_ID, 2.0)))
            if CUSTOM_MESSAGE:
                try:
                    if CUSTOM_MESSAGE_TYPE == "text":
                        await bot.send_message(CHANNEL_ID, CUSTOM_MESSAGE_CONTENT)
                    elif CUSTOM_MESSAGE_TYPE == "photo":
                        await bot.send_photo(CHANNEL_ID, CUSTOM_MESSAGE_CONTENT["file_id"], caption=CUSTOM_MESSAGE_CONTENT.get("caption"))
                    elif CUSTOM_MESSAGE_TYPE == "video":
                        await bot.send_video(CHANNEL_ID, CUSTOM_MESSAGE_CONTENT["file_id"], caption=CUSTOM_MESSAGE_CONTENT.get("caption"))
                    elif CUSTOM_MESSAGE_TYPE == "animation":
                        await bot.send_animation(CHANNEL_ID, CUSTOM_MESSAGE_CONTENT["file_id"], caption=CUSTOM_MESSAGE_CONTENT.get("caption"))
                except Exception as e:
                    print("❌ Error sending custom message:", e)
            await asyncio.sleep(3600)
        else:
            await asyncio.sleep(10)

@dp.message(F.text == "/setcustom")
async def set_custom_message(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.reply("📥 Send the message (text/photo/video/gif) that should be sent after 15 predictions.")
    dp.message.register(capture_custom_message)

async def capture_custom_message(message: types.Message):
    global CUSTOM_MESSAGE, CUSTOM_MESSAGE_TYPE, CUSTOM_MESSAGE_CONTENT
    CUSTOM_MESSAGE = True
    if message.text:
        CUSTOM_MESSAGE_TYPE = "text"
        CUSTOM_MESSAGE_CONTENT = message.text
    elif message.photo:
        CUSTOM_MESSAGE_TYPE = "photo"
        CUSTOM_MESSAGE_CONTENT = {"file_id": message.photo[-1].file_id, "caption": message.caption}
    elif message.video:
        CUSTOM_MESSAGE_TYPE = "video"
        CUSTOM_MESSAGE_CONTENT = {"file_id": message.video.file_id, "caption": message.caption}
    elif message.animation:
        CUSTOM_MESSAGE_TYPE = "animation"
        CUSTOM_MESSAGE_CONTENT = {"file_id": message.animation.file_id, "caption": message.caption}
    await message.reply("✅ Custom message saved.")

@dp.message(F.text == "/deletecustom")
async def delete_custom_message(message: types.Message):
    global CUSTOM_MESSAGE, CUSTOM_MESSAGE_TYPE, CUSTOM_MESSAGE_CONTENT
    if message.from_user.id != ADMIN_ID:
        return
    CUSTOM_MESSAGE = None
    CUSTOM_MESSAGE_TYPE = None
    CUSTOM_MESSAGE_CONTENT = None
    await message.reply("🗑️ Custom message deleted.")

# /startpredict
@dp.message(F.text == "/startpredict")
async def start_predicting(message: types.Message):
    global prediction_task, is_running
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ You are not allowed.")
    if is_running:
        return await message.reply("⚠️ Prediction already running.")
    await message.reply("✅ Prediction started.")
    prediction_task = asyncio.create_task(prediction_loop(message.chat.id))

# /stoppredict
@dp.message(F.text == "/stoppredict")
async def stop_predicting(message: types.Message):
    global prediction_task, is_running
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ You are not allowed.")
    is_running = False
    if prediction_task:
        prediction_task.cancel()
    await message.reply("🛑 Prediction stopped.")

# Save Win files
@dp.message(F.chat.type == ChatType.PRIVATE, F.text == "/file")
async def handle_file_command(message: types.Message):
    await message.answer("📎 Send me any sticker, photo, or gif to use as WIN sticker when 'Pass' is clicked.")

@dp.message(F.chat.type == ChatType.PRIVATE, F.content_type.in_(["sticker", "photo", "animation"]))
async def save_file_id(message: types.Message):
    file_id = message.sticker.file_id if message.sticker else \
              message.photo[-1].file_id if message.photo else \
              message.animation.file_id if message.animation else None
    if file_id:
        WIN_STICKERS.append(file_id)
        await message.reply("✅ File saved!")
    else:
        await message.reply("❌ Unable to save file.")

# Pass/Fail
@dp.callback_query(F.data.in_({"pass", "fail"}))
async def handle_button(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    if callback.data == "pass":
        if WIN_STICKERS:
            try:
                await bot.send_sticker(chat_id, random.choice(WIN_STICKERS))
            except: pass
        delay = calculate_delay(LAST_MULTIPLIER.get(chat_id, 1.11))
        await callback.answer(f"✅ Pass selected.\n⏳ Please wait {delay}s", show_alert=True)
        await asyncio.sleep(delay)
        await send_prediction(chat_id)
    elif callback.data == "fail":
        delay = calculate_delay(CRASH_MULTIPLIER.get(chat_id, 1.11))
        await callback.answer(f"❌ Crash occurred!\n⏳ Please wait {delay}s", show_alert=True)
        await asyncio.sleep(delay)
        await send_prediction(chat_id)

# /setchannel
@dp.message(F.chat.type == ChatType.PRIVATE, F.text == "/setchannel")
async def set_channel(message: types.Message):
    await message.reply("📣 Send your channel @username or numeric ID")
    dp.message.register(awaiting_channel_input)

async def awaiting_channel_input(message: types.Message):
    global CHANNEL_ID
    CHANNEL_ID = message.text.strip()
    await message.answer(f"✅ Channel set to: <code>{CHANNEL_ID}</code>")

# /sendpredict
@dp.message(F.chat.type == ChatType.PRIVATE, F.text == "/sendpredict")
async def send_prediction_to_channel(message: types.Message):
    if not CHANNEL_ID:
        return await message.reply("❌ Channel not set. Use /setchannel")
    await send_prediction(CHANNEL_ID)
    await message.reply("✅ Prediction sent to channel.")

# Start
async def main():
    asyncio.create_task(channel_prediction_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
