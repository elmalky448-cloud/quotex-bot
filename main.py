import os
import threading
import uvicorn
from fastapi import FastAPI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Bot is running"}

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 بوت Quotex شغال تمام يا مالكي! ✅\n\nالبوت جاهز ويبعت اشارات\n\nجرب /status")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 البوت شغال وبيفحص السوق...")

def run_api():
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

# شغل الـ API في الخلفية
threading.Thread(target=run_api, daemon=True).start()

# شغل بوت التليجرام في الخيط الرئيسي (ده الحل)
if BOT_TOKEN:
    print(f"✅ Starting Telegram Bot with token...")
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("status", status_cmd))
    print("🤖 Bot polling started - waiting for /start")
    application.run_polling()
else:
    print("❌ NO BOT_TOKEN")
    run_api()