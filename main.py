import os
import threading
from fastapi import FastAPI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import uvicorn

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8000))

# ده اللي Koyeb بيدور عليه عشان ميعملش ERROR
app = FastAPI()

@app.get("/")
def home():
    return {"status": "Bot is running"}

# --- كود البوت ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ البوت شغال تمام!\nجرب /signal EURUSD")

async def pairs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("EURUSD GBPUSD USDJPY AUDUSD BTCUSD GOLD")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pair = context.args[0].upper() if context.args else "EURUSD"
    await update.message.reply_text(f"🔍 بحلل {pair}...")
    try:
        import yfinance as yf
        import ta
        mp = {"EURUSD":"EURUSD=X","GBPUSD":"GBPUSD=X","USDJPY":"JPY=X","AUDUSD":"AUDUSD=X","BTCUSD":"BTC-USD","GOLD":"GC=F"}
        sym = mp.get(pair, f"{pair}=X")
        df = yf.download(sym, period="1d", interval="5m", progress=False)
        if df.empty or len(df) < 30:
            await update.message.reply_text("مفيش بيانات")
            return
        c = df['Close']
        price = float(c.iloc[-1])
        rsi = float(ta.momentum.RSIIndicator(c, 14).rsi().iloc[-1])
        sig = "CALL ⬆️" if rsi < 50 else "PUT ⬇️"
        await update.message.reply_text(f"📊 {pair}\n💵 {price:.5f}\nRSI {rsi:.1f}\n📈 {sig}")
    except Exception as e:
        await update.message.reply_text(f"خطأ: {e}")

def run_bot():
    print(f"Token exists: {bool(BOT_TOKEN)}")
    if not BOT_TOKEN:
        print("NO TOKEN - Bot not started")
        return
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("pairs", pairs))
    bot_app.add_handler(CommandHandler("signal", signal))
    print("Bot Polling Started...")
    bot_app.run_polling()

# شغل البوت في الخلفية مع الموقع
threading.Thread(target=run_bot, daemon=True).start()