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
    return {"status": "PRO Bot Running"}

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 بوت التحليل القوي PRO جاهز!\n\n"
        "📊 بيحلل بـ 6 طرق:\n"
        "1️⃣ RSI + Stochastic\n"
        "2️⃣ EMA 9/21/50\n"
        "3️⃣ MACD\n"
        "4️⃣ Bollinger Bands\n"
        "5️⃣ Price Action\n"
        "6️⃣ دعم ومقاومة\n\n"
        "الاوامر:\n"
        "/signal EURUSD\n"
        "/signal BTCUSD\n"
        "/signal GOLD\n"
        "/pairs"
    )

async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ مثال: /signal EURUSD")
        return
    pair = context.args[0].upper()
    await update.message.reply_text(f"🔍 بعمل تحليل عميق لـ {pair}... 10 ثواني")

    try:
        import yfinance as yf
        import ta
        import pandas as pd

        symbol_map = {
            "EURUSD":"EURUSD=X","GBPUSD":"GBPUSD=X","USDJPY":"JPY=X",
            "AUDUSD":"AUDUSD=X","USDCAD":"USDCAD=X","EURJPY":"EURJPY=X",
            "BTCUSD":"BTC-USD","GOLD":"GC=F","ETHUSD":"ETH-USD"
        }
        yf_symbol = symbol_map.get(pair, f"{pair}=X")
        data = yf.download(yf_symbol, period="2d", interval="5m", progress=False)

        if len(data) < 100:
            await update.message.reply_text("❌ بيانات غير كافية")
            return

        close = data['Close']
        high = data['High']
        low = data['Low']
        price = float(close.iloc[-1])

        # 1. RSI
        rsi = float(ta.momentum.RSIIndicator(close, 14).rsi().iloc[-1])
        # 2. Stochastic
        stoch = ta.momentum.StochasticOscillator(high, low, close)
        stoch_k = float(stoch.stoch().iloc[-1])
        # 3. EMA
        ema9 = float(ta.trend.EMAIndicator(close, 9).ema_indicator().iloc[-1])
        ema21 = float(ta.trend.EMAIndicator(close, 21).ema_indicator().iloc[-1])
        ema50 = float(ta.trend.EMAIndicator(close, 50).ema_indicator().iloc[-1])
        # 4. MACD
        macd_line = ta.trend.MACD(close)
        macd = float(macd_line.macd().iloc[-1])
        macd_signal = float(macd_line.macd_signal().iloc[-1])
        # 5. Bollinger
        bb = ta.volatility.BollingerBands(close)
        bb_upper = float(bb.bollinger_hband().iloc[-1])
        bb_lower = float(bb.bollinger_lband().iloc[-1])
        # 6. Price Action - اخر شمعتين
        last_candle = data.iloc[-1]
        prev_candle = data.iloc[-2]
        bullish_engulfing = float(last_candle['Close']) > float(last_candle['Open']) and float(prev_candle['Close']) < float(prev_candle['Open'])

        # حساب نقاط القوة
        buy_score = 0
        sell_score = 0
        reasons = []

        if rsi < 40: buy_score+=1; reasons.append(f"RSI قليل {rsi:.0f} (تشبع بيع)")
        if rsi > 60: sell_score+=1; reasons.append(f"RSI عالي {rsi:.0f} (تشبع شراء)")
        if stoch_k < 25: buy_score+=1; reasons.append(f"Stochastic {stoch_k:.0f} بيع مفرط")
        if stoch_k > 75: sell_score+=1; reasons.append(f"Stochastic {stoch_k:.0f} شراء مفرط")
        if ema9 > ema21 > ema50: buy_score+=2; reasons.append("EMA صاعد قوي 9>21>50")
        if ema9 < ema21 < ema50: sell_score+=2; reasons.append("EMA هابط قوي 9<21<50")
        elif ema9 > ema21: buy_score+=1; reasons.append("EMA9 فوق EMA21")
        elif ema9 < ema21: sell_score+=1; reasons.append("EMA9 تحت EMA21")
        if macd > macd_signal: buy_score+=1; reasons.append("MACD صاعد")
        else: sell_score+=1; reasons.append("MACD هابط")
        if price < bb_lower*1.001: buy_score+=1; reasons.append("السعر عند الحد السفلي Bollinger")
        if price > bb_upper*0.999: sell_score+=1; reasons.append("السعر عند الحد العلوي Bollinger")
        if bullish_engulfing: buy_score+=1; reasons.append("شمعة ابتلاعية صاعدة")

        total = buy_score + sell_score
        if buy_score >= 4 and buy_score > sell_score*1.5:
            signal = "صعود قوي CALL ⬆️⬆️"
            conf = min(95