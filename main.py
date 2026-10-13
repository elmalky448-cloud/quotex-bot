import os
import threading
from fastapi import FastAPI
from telegram.ext import ApplicationBuilder, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

app = FastAPI()

@app.get("/")
def root():
    return {"status": "Bot Running"}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 بوت Quotex شغال تمام يا مالكي! ✅\n\nالبوت بيستنى اشارة قوية وهيبعتلك\n\nجرب /status")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 البوت شغال وبيفحص السوق...")

def start_bot():
    if not BOT_TOKEN:
        print("No BOT_TOKEN found!")
        return
    print("Starting Telegram Bot...")
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("status", status))
    app_bot.run_polling()

threading.Thread(target=start_bot, daemon=True).start()