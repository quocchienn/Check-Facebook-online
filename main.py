import os
import requests
from flask import Flask
from threading import Thread

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ===== CONFIG =====
BOT_TOKEN = os.getenv("BOT_TOKEN")

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

# ===== FACEBOOK INFO =====
def get_facebook_info(url):
    try:
        api = f"https://id.traodoisub.com/api.php?link={url}"
        res = requests.get(api, timeout=10).json()

        return {
            "uid": res.get("id"),
            "name": res.get("name"),
            "avatar": res.get("avatar")
        }
    except:
        return None

# ===== TELEGRAM HANDLERS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Gửi link Facebook để lấy UID + thông tin public"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "facebook.com" not in url:
        await update.message.reply_text("❌ Link không hợp lệ")
        return

    await update.message.reply_text("⏳ Đang xử lý...")

    data = get_facebook_info(url)

    if not data or not data["uid"]:
        await update.message.reply_text("❌ Không lấy được dữ liệu (có thể bị ẩn)")
        return

    msg = f"""
👤 Tên: {data['name']}
🆔 UID: {data['uid']}
"""

    try:
        if data["avatar"]:
            await update.message.reply_photo(photo=data["avatar"], caption=msg)
        else:
            await update.message.reply_text(msg)
    except:
        await update.message.reply_text(msg)

# ===== MAIN =====
def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot started...")
    app.run_polling()

if __name__ == "__main__":
    keep_alive()
    run_bot()
