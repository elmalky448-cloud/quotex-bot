import os, threading, time
from fastapi import FastAPI
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN")
app = FastAPI()
bot = telebot.TeleBot(BOT_TOKEN, threaded=False) if BOT_TOKEN else None

@app.get("/")
def home(): return {"status":"REAL MARKET ONLY"}

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "✅ بوت تحليل سوق حقيقي 100%\n\nممنوع OTC\nجرب:\n/signal EURUSD\n/signal GBPUSD\n/signal USDJPY\n/signal BTCUSD\n/signal GOLD\n\nده سوق فوركس الحقيقي")

@bot.message_handler(commands=['signal'])
def signal(m):
    parts = m.text.split()
    raw_pair = parts[1].upper() if len(parts) > 1 else "EURUSD"

    if "OTC" in raw_pair:
        bot.reply_to(m, f"❌ {raw_pair} ده سوق وهمي من Quotex مش سوق حقيقي\n\nمقدرش احلله تحليل حقيقي\nجرب:\n/signal EURUSD\n/signal GBPUSD\nده سوق حقيقي")
        return

    pair = raw_pair
    bot.reply_to(m, f"🔍 بجيب بيانات حية لـ {pair} من سوق الفوركس الحقيقي...")

    try:
        import yfinance as yf
        import pandas as pd
        import numpy as np

        # تحديد الرمز الحقيقي
        symbol_map = {
            "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "USDJPY": "USDJPY=X",
            "AUDUSD": "AUDUSD=X", "USDCAD": "USDCAD=X", "GOLD": "GC=F",
            "XAUUSD": "GC=F", "BTCUSD": "BTC-USD", "BTC": "BTC-USD"
        }
        yf_symbol = symbol_map.get(pair, f"{pair}=X")

        df = yf.download(yf_symbol, period="5d", interval="1m", progress=False, auto_adjust=True)

        if df.empty or len(df) < 50:
            bot.reply_to(m, f"⚠️ السوق قافل حاليا لـ {pair}\nالفوركس بيقفل الجمعة 10 بليل ويفتح الاتنين\nجرب وقت السوق")
            return

        close = df['Close']
        high = df['High']
        low = df['Low']
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:,0]
            high = high.iloc[:,0]
            low = low.iloc[:,0]

        close = close.dropna()
        high = high.dropna()
        low = low.dropna()

        price = float(close.iloc[-1])

        # 1. RSI حقيقي
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_val = float(rsi.iloc[-1])

        # 2. EMA
        ema9 = float(close.ewm(span=9).mean().iloc[-1])
        ema21 = float(close.ewm(span=21).mean().iloc[-1])
        ema50 = float(close.ewm(span=50).mean().iloc[-1])

        # 3. MACD
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd = ema12 - ema26
        macd_signal = macd.ewm(span=9).mean()
        macd_val = float(macd.iloc[-1])
        macd_sig_val = float(macd_signal.iloc[-1])

        # 4. Stochastic
        low14 = low.rolling(14).min()
        high14 = high.rolling(14).max()
        k_percent = 100 * ((close - low14) / (high14 - low14))
        k_val = float(k_percent.iloc[-1])

        # القرار - تحليل حقيقي بدون عشوائية
        bullish_signals = 0
        bearish_signals = 0
        reasons = []

        if rsi_val < 30:
            bullish_signals += 2
            reasons.append(f"RSI تشبع بيعي {rsi_val:.1f}")
        elif rsi_val > 70:
            bearish_signals += 2
            reasons.append(f"RSI تشبع شرائي {rsi_val:.1f}")
        elif rsi_val < 50:
            bullish_signals += 1
        else:
            bearish_signals += 1

        if ema9 > ema21 > ema50:
            bullish_signals += 2
            reasons.append("EMA ترند صاعد قوي")
        elif ema9 < ema21 < ema50:
            bearish_signals += 2
            reasons.append("EMA ترند هابط قوي")
        elif ema9 > ema21:
            bullish_signals += 1
            reasons.append("EMA9 فوق EMA21")
        else:
            bearish_signals += 1
            reasons.append("EMA9 تحت EMA21")

        if macd_val > macd_sig_val:
            bullish_signals += 1
            reasons.append("MACD صاعد")
        else:
            bearish_signals += 1
            reasons.append("MACD هابط")

        if k_val < 20:
            bullish_signals += 1
            reasons.append(f"Stochastic تشبع بيعي {k_val:.0f}")
        elif k_val > 80:
            bearish_signals += 1
            reasons.append(f"Stochastic تشبع شرائي {k_val:.0f}")

        # النتيجة النهائية
        if bullish_signals >= 4:
            sig = "CALL قوي ⬆️⬆️"
            conf = "85-90%"
        elif bearish_signals >= 4:
            sig = "PUT قوي ⬇️⬇️"
            conf = "85-90%"
        elif bullish_signals > bearish_signals:
            sig = "CALL ⬆️"
            conf = "70-78%"
        elif bearish_signals > bullish_signals:
            sig = "PUT ⬇️"
            conf = "70-78%"
        else:
            sig = "انتظار - السوق عرضي"
            conf = "50%"

        msg = f"""📊 تحليل حقيقي {pair}
المصدر: سوق الفوركس العالمي - Yahoo Finance

💵 السعر الحي: {price:.5f}

📈 المؤشرات الحقيقية:
• RSI(14): {rsi_val:.1f}
• EMA9/21/50: {ema9:.5f} / {ema21:.5f} / {ema50:.5f}
• MACD: {macd_val:.5f} vs {macd_sig_val:.5f}
• Stochastic: {k_val:.1f}

📋 الأسباب:
{chr(10).join(['• '+r for r in reasons])}

🎯 الإشارة: {sig}
🔒 القوة: {conf}
⏰ الفريم: 1-3 دقايق
⚠️ ده تحليل فني حقيقي مش توصية

جرب زوج تاني /signal GBPUSD"""

        bot.reply_to(m, msg)

    except Exception as e:
        print(f"ERROR: {e}")
        bot.reply_to(m, f"خطأ في جلب البيانات: {e}\nالسوق ممكن يكون قافل")

def run_bot():
    while True:
        try: bot.infinity_polling(timeout=30, long_polling_timeout=60)
        except Exception as e:
            print(e)
            time.sleep(5)

if BOT_TOKEN: threading.Thread(target=run_bot, daemon=True).start()