import os
import threading
import uvicorn
import yfinance as yf
import pandas as pd
import ta
from fastapi import FastAPI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
app = FastAPI()

@app.get("/")
def home():
    return {"status": "Quotex Bot Running"}

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 بوت Quotex للاشارات جاهز!\n\n"
        "📊 الاوامر:\n"
        "/signal EURUSD - تحليل زوج\n"
        "/signal BTCUSD - تحليل بيتكوين\n"
        "/pairs - اهم الازواج\n\n"
        "مثال: /signal EURUSD"
    )

async def pairs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 اهم الازواج للتداول:\n"
        "EURUSD - USDJPY - GBPUSD\n"
        "AUDUSD - USDCAD - EURJPY\n"
        "BTCUSD - GOLD\n\n"
        "استخدم: /signal + اسم الزوج"
    )

async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ ابعت كده: /signal EURUSD")
        return

    pair = context.args[0].upper()
    # تحويل لصيغة yfinance
    symbol_map = {
        "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "USDJPY": "JPY=X",
        "AUDUSD": "AUDUSD=X", "BTCUSD": "BTC-USD", "GOLD": "GC=F"
    }
    yf_symbol = symbol_map.get(pair, f"{pair}=X")

    await update.message.reply_text(f"⏳ بحلل {pair}... ثواني")

    try:
        data = yf.download(yf_symbol, period="1d", interval="1m", progress=False)
        if len(data) < 50:
            await update.message.reply_text("❌ مفيش بيانات كفاية للزوج ده")
            return

        close = data['Close']

        # مؤشرات قوية
        rsi = ta.momentum.RSIIndicator(close).rsi().iloc[-1]
        ema9 = ta.trend.EMAIndicator(close, window=9).ema_indicator().iloc[-1]
        ema21 = ta.trend.EMAIndicator(close, window=21).ema_indicator().iloc[-1]
        price = float(close.iloc[-1])

        # منطق الاشارة
        if rsi < 35 and ema9 > ema21:
            signal = "صعود CALL ⬆️"
            strength = 85 + (35 - rsi)
        elif rsi > 65 and ema9 < ema21:
            signal = "هبوط PUT ⬇️"
            strength = 85 + (rsi - 65)
        elif ema9 > ema21 and rsi > 50:
            signal = "صعود CALL ⬆️"
            strength = 75
        elif ema9 < ema21 and rsi < 50:
            signal = "هبوط PUT ⬇️"
            strength = 75
        else:
            signal = "انتظار ⏸️ السوق متذبذب"
            strength = 50

        strength = min(95, int(strength))

        msg = (
            f"📊 تحليل {pair}\n"
            f"━━━━━━━━━━━━\n"
            f"💵 السعر: {price:.5f}\n"
            f"📈 الاشارة: {signal}\n"
            f"💪 القوة: {strength}%\n"
            f"📉 RSI: {rsi:.1f}\n"
            f"〰️ EMA9/21