import os
import asyncio
import requests
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from aiohttp import web

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("OPENROUTER_API_KEY")
PORT = int(os.environ.get("PORT", 10000))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_mode = {}

# ===== MENU =====
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Chat AI", callback_data="chat")],
        [InlineKeyboardButton(text="🖼️ Tạo ảnh", callback_data="image")],
        [InlineKeyboardButton(text="🎬 Tạo video", callback_data="video")]
    ])

# ===== START =====
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🚀 Bot AI sẵn sàng!", reply_markup=main_menu())

# ===== BUTTON =====
@dp.callback_query()
async def callback(call: types.CallbackQuery):
    user_mode[call.from_user.id] = call.data
    await call.message.answer(f"👉 Bạn chọn: {call.data}\nNhập nội dung:")

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

# ===== IMAGE =====
def generate_image(prompt):
    return f"https://image.pollinations.ai/prompt/{prompt}"

# ===== VIDEO (demo) =====
def generate_video(prompt):
    return f"https://dummyvideo.com/?text={prompt}"

# ===== HANDLE MESSAGE =====
@dp.message(F.text)
async def handle_message(message: types.Message):
    mode = user_mode.get(message.from_user.id)

    if not mode:
        await message.answer("❌ Chọn chức năng trước", reply_markup=main_menu())
        return

    if mode == "chat":
        await message.answer("🤖 Đang xử lý...")
        try:
            reply = chat_ai(message.text)
            await message.answer(reply)
        except:
            await message.answer("❌ Lỗi API")

    elif mode == "image":
        img = generate_image(message.text)
        await message.answer_photo(img)

    elif mode == "video":
        vid = generate_video(message.text)
        await message.answer(f"🎬 Video:\n{vid}")

# ===== WEB SERVER =====
async def handle(request):
    return web.Response(text="Bot is running")

async def start_web():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

# ===== MAIN =====
async def main():
    await start_web()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
