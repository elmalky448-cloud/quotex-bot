import os, threading, time
from fastapi import FastAPI
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN")
print(f"TOKEN: {bool(BOT_TOKEN)}")

app = FastAPI()
bot = telebot.TeleBot(BOT_TOKEN, threaded=False) if BOT_TOKEN else None

@app.get("/")
def home():
    return {"status": "Bot is LIVE"}

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "✅ البوت شغال 100%!\n\nجرب:\n/signal EURUSD\n/pairs")

@bot.message_handler(commands=['pairs'])
def pairs(m):
    bot.reply_to(m, "EURUSD GBPUSD USDJPY AUDUSD BTCUSD GOLD")

@bot.message_handler(commands=['signal'])
def signal(m):
    try:
        parts = m.text.split()
        pair = parts[1].upper() if len(parts) > 1 else "EURUSD"
        bot.reply_to(m, f"🔍 بحلل {pair}...")
        import yfinance as yf
        df = yf.download(f"{pair}=X", period="1d", interval="5m", progress=False)
        close = df['Close']
        price = float(close.iloc[-1])
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rs = gain / loss
        rsi = float(100 - (100 / (1 + rs.iloc[-1])))

        sig = "CALL ⬆️" if rsi < 50 else "PUT ⬇️"
        if rsi < 30: sig = "CALL قوي ⬆️⬆️"
        if rsi > 70: sig = "PUT قوي ⬇️⬇️"

        bot.reply_to(m, f"📊 {pair}\n💵 {price:.5f}\nRSI: {rsi:.1f}\n📈 {sig}\n⏰ 3 دق - Quotex PRO")
    except Exception as e:
        print(e)
        bot.reply_to(m, f"خطأ: {e}")

def run_bot():
    print("Bot polling started...")
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except Exception as e:
            print(f"poll error {e}, retry in 5s")
            time.sleep(5)

if BOT_TOKEN:
    threading.Thread(target=run_bot, daemon=True).start()