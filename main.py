import asyncio
import random
import time
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.enums.chat_type import ChatType
from aiogram import F
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = "8024704510:AAFSyhxNfACt0nEg59dYgrxi71najTIZil4"
ADMIN_ID = 6484788124  # 🔁 Replace with your numeric Telegram ID

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Global States
WIN_STICKERS = []
LAST_MULTIPLIER = {}
CRASH_MULTIPLIER = {}
prediction_task = None
is_running = False

# Helper: Make multiplier fancy
def fancy_multiplier(x):
    normal = "0123456789x."
    fancy = "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵𝘅․"
    return "".join(fancy[normal.index(c)] if c in normal else c for c in f"{x}x")

# Aviator timing logic
def calculate_delay(multiplier):
    if multiplier <= 1.00:
        return 0
    return int(((multiplier - 1.00) / 0.11) * 3)

# Generate prediction and set crash value
def get_prediction():
    emojis = ["🔥", "✈️", "💨", "⚡", "𞥂", "🌪️"]
    emoji = random.choice(emojis)
    multiplier = round(random.uniform(1.00, 5.00), 2)
    crash = round(random.uniform(1.01, multiplier), 2)

    prediction_text = f"{emoji} <b>Aviator Spribe</b>\n<b>{fancy_multiplier(multiplier)}</b>"
    footer = (
        "\n\n<blockquote>🎮 Play at your own risk</blockquote>"
        "<blockquote>🛡️ Maintain Level 1 to 3</blockquote>"
        "<blockquote>🔗 Register with our official link, otherwise hack will not work.</blockquote>\n"
        "<a href='https://bdgslotclub.com/#/register?inviteCode=46377313830'>🚀 Click here to Register</a>"
    )

    return prediction_text + footer, multiplier, crash

# Send prediction with buttons
async def send_prediction(chat_id):
    prediction_text, multiplier, crash = get_prediction()
    LAST_MULTIPLIER[chat_id] = multiplier
    CRASH_MULTIPLIER[chat_id] = crash

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Pass", callback_data="pass"),
         InlineKeyboardButton(text="❌ Crash", callback_data="fail")]
    ])
    await bot.send_message(chat_id, prediction_text, reply_markup=keyboard)

# Prediction loop (admin only)
async def prediction_loop(chat_id):
    global is_running
    is_running = True
    while is_running:
        await send_prediction(chat_id)
        multiplier = LAST_MULTIPLIER.get(chat_id, 2.0)
        delay = calculate_delay(multiplier)
        await asyncio.sleep(delay)

# Start prediction — admin
@dp.message(F.text == "/startpredict")
async def start_predicting(message: types.Message):
    global prediction_task, is_running
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ You are not allowed.")
    if is_running:
        return await message.reply("⚠️ Prediction already running.")
    await message.reply("✅ Prediction started.")
    prediction_task = asyncio.create_task(prediction_loop(message.chat.id))

# Stop prediction — admin
@dp.message(F.text == "/stoppredict")
async def stop_predicting(message: types.Message):
    global prediction_task, is_running
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ You are not allowed.")
    is_running = False
    if prediction_task:
        prediction_task.cancel()
    await message.reply("🛑 Prediction stopped.")

# Save WIN file (sticker/photo/gif)
@dp.message(F.chat.type == ChatType.PRIVATE, F.text == "/file")
async def handle_file_command(message: types.Message):
    await message.answer("📎 Send me any sticker, photo, or gif to use as WIN sticker when 'Pass' is clicked.")

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

# Handle Pass / Fail button clicks
@dp.callback_query(F.data.in_({"pass", "fail"}))
async def handle_button(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id

    if callback.data == "pass":
        if WIN_STICKERS:
            try:
                sticker = random.choice(WIN_STICKERS)
                await bot.send_sticker(chat_id, sticker)
            except Exception as e:
                print("Sticker send failed:", e)

        multiplier = LAST_MULTIPLIER.get(chat_id, 1.11)
        delay = calculate_delay(multiplier)
        await callback.answer(f"✅ Pass selected.\n⏳ Please wait {delay}s", show_alert=True)
        await asyncio.sleep(delay)
        await send_prediction(chat_id)

    elif callback.data == "fail":
        crash_multiplier = CRASH_MULTIPLIER.get(chat_id, 1.11)
        delay = calculate_delay(crash_multiplier)
        await callback.answer(f"❌ Crash occurred!\n⏳ Please wait {delay}s", show_alert=True)
        await asyncio.sleep(delay)
        await send_prediction(chat_id)

# Launch the bot
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
