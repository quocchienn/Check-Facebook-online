import os
from flask import Flask
import requests
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("OPENROUTER_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ===== MENU =====
def main_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Chat AI", callback_data="chat")],
        [InlineKeyboardButton(text="🖼️ Tạo ảnh", callback_data="image")],
        [InlineKeyboardButton(text="🎬 Tạo video", callback_data="video")]
    ])
    return kb

# ===== START =====
@dp.message(commands=["start"])
async def start(message: types.Message):
    await message.answer("🚀 Bot AI đã sẵn sàng!", reply_markup=main_menu())

# ===== CALLBACK =====
user_mode = {}

@dp.callback_query()
async def handle_callback(call: types.CallbackQuery):
    user_mode[call.from_user.id] = call.data
    await call.message.answer(f"👉 Bạn chọn: {call.data}\nHãy nhập nội dung:")

# ===== AI CHAT =====
def chat_ai(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openrouter/auto",
        "messages": [{"role": "user", "content": prompt}]
    }
    res = requests.post(url, headers=headers, json=data)
    return res.json()["choices"][0]["message"]["content"]

# ===== IMAGE AI (free API demo) =====
def generate_image(prompt):
    return f"https://image.pollinations.ai/prompt/{prompt}"

# ===== VIDEO AI (placeholder) =====
def generate_video(prompt):
    # bạn có thể thay bằng API thật sau
    return f"https://dummyvideo.com/result?text={prompt}"

# ===== HANDLE MESSAGE =====
@dp.message()
async def handle_message(message: types.Message):
    mode = user_mode.get(message.from_user.id)

    if not mode:
        await message.answer("❌ Hãy chọn chức năng trước!", reply_markup=main_menu())
        return

    if mode == "chat":
        await message.answer("🤖 Đang suy nghĩ...")
        reply = chat_ai(message.text)
        await message.answer(reply)

    elif mode == "image":
        img_url = generate_image(message.text)
        await message.answer_photo(img_url)

    elif mode == "video":
        vid_url = generate_video(message.text)
        await message.answer(f"🎬 Video của bạn:\n{vid_url}")
# ===== KEEP ALIVE WEB (Render cần port) =====
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()
# ===== RUN =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
