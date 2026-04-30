import os
import requests
import asyncio
import aiofiles
import threading
from flask import Flask
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ==== CONFIG ====
TOKEN = os.getenv("BOT_TOKEN")
MAX_CONCURRENT = 10
DELAY = 0.5

semaphore = asyncio.Semaphore(MAX_CONCURRENT)

# ==== WEB SERVER (ANTI SLEEP RENDER) ====
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web).start()

# ==== CHECK FACEBOOK ====
async def check_facebook(uid):
    url = f"https://www.facebook.com/{uid}"
    headers = {"User-Agent": "Mozilla/5.0"}

    async with semaphore:
        await asyncio.sleep(DELAY)
        try:
            r = requests.get(url, headers=headers, timeout=10)

            if "login" in r.url:
                return uid, "checkpoint"
            elif "not found" in r.text.lower():
                return uid, "die"
            elif "disabled" in r.text.lower():
                return uid, "banned"
            else:
                return uid, "live"
        except:
            return uid, "error"

# ==== PROCESS RESULT ====
async def process_results(update, results):
    live, die, checkpoint, error = [], [], [], []

    for uid, status in results:
        if status == "live":
            live.append(uid)
        elif status == "die":
            die.append(uid)
        elif status == "checkpoint":
            checkpoint.append(uid)
        else:
            error.append(uid)

    async def write_file(name, data):
        async with aiofiles.open(name, "w") as f:
            await f.write("\n".join(data))

    await write_file("live.txt", live)
    await write_file("die.txt", die)
    await write_file("checkpoint.txt", checkpoint)

    msg = (
        f"📊 KẾT QUẢ\n\n"
        f"✅ Live: {len(live)}\n"
        f"❌ Die: {len(die)}\n"
        f"⚠️ Checkpoint: {len(checkpoint)}\n"
        f"⛔ Error: {len(error)}"
    )

    await update.message.reply_text(msg)

    if live:
        await update.message.reply_document(InputFile("live.txt"))
    if die:
        await update.message.reply_document(InputFile("die.txt"))
    if checkpoint:
        await update.message.reply_document(InputFile("checkpoint.txt"))

# ==== HANDLE TEXT ====
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uids = [u.strip() for u in text.split("|") if u.strip()]

    if not uids:
        await update.message.reply_text("❌ Không có UID hợp lệ")
        return

    await update.message.reply_text(f"⏳ Đang check {len(uids)} UID...")

    tasks = [check_facebook(uid) for uid in uids]
    results = await asyncio.gather(*tasks)

    await process_results(update, results)

# ==== HANDLE FILE TXT ====
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    path = "uids.txt"
    await file.download_to_drive(path)

    async with aiofiles.open(path, "r") as f:
        content = await f.read()

    uids = [u.strip() for u in content.splitlines() if u.strip()]

    if not uids:
        await update.message.reply_text("❌ File không có UID")
        return

    await update.message.reply_text(f"📂 File có {len(uids)} UID, đang check...")

    tasks = [check_facebook(uid) for uid in uids]
    results = await asyncio.gather(*tasks)

    await process_results(update, results)

# ==== START ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 FB CHECK BOT PRO\n\n"
        "📌 Hướng dẫn:\n"
        "- Gửi UID dạng: uid|uid|uid\n"
        "- Hoặc upload file .txt"
    )

# ==== MAIN ====
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
