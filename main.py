import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 بوت Quotex PRO شغال!\n\n"
        "/signal EURUSD - تحليل قوي\n"
        "/pairs - الازواج"
    )

async def pairs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("EURUSD GBPUSD USDJPY AUDUSD BTCUSD GOLD")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("استخدم: /signal EURUSD")
        return
    pair = context.args[0].upper()
    await update.message.reply_text(f"🔍 بحلل {pair}...")
    try:
        import yfinance as yf
        import ta

        mp = {"EURUSD":"EURUSD=X","GBPUSD":"GBPUSD=X","USDJPY":"JPY=X","AUDUSD":"AUDUSD=X","BTCUSD":"BTC-USD","GOLD":"GC=F"}
        sym = mp.get(pair, f"{pair}=X")
        df = yf.download(sym, period="2d", interval="5m", progress=False)
        if len(df) < 50:
            await update.message.reply_text("مفيش بيانات كفاية")
            return

        c = df['Close']; h = df['High']; l = df['Low']
        price = float(c.iloc[-1])
        rsi = float(ta.momentum.RSIIndicator(c, 14).rsi().iloc[-1])
        ema9 = float(ta.trend.EMAIndicator(c, 9).ema_indicator().iloc[-1])
        ema21 = float(ta.trend.EMAIndicator(c, 21).ema_indicator().iloc[-1])
        ema50 = float(ta.trend.EMAIndicator(c, 50).ema_indicator().iloc[-1])
        macd_obj = ta.trend.MACD(c)
        macd = float(macd_obj.macd().iloc[-1])
        macd_s = float(macd_obj.macd_signal().iloc[-1])
        stoch = float(ta.momentum.StochasticOscillator(h,l,c).stoch().iloc[-1])
        bb = ta.volatility.BollingerBands(c)
        bb_l = float(bb.bollinger_lband().iloc[-1])
        bb_u = float(bb.bollinger_hband().iloc[-1])

        buy=0; sell=0; rs=[]
        if rsi<40: buy+=1; rs.append(f"RSI {rsi:.0f} بيع مفرط")
        if rsi>60: sell+=1; rs.append(f"RSI {rsi:.0f} شراء مفرط")
        if stoch<25: buy+=1; rs.append(f"Stoch {stoch:.0f} بيع مفرط")
        if stoch>75: sell+=1; rs.append(f"Stoch {stoch:.0f} شراء مفرط")
        if ema9>ema21>ema50: buy+=2; rs.append("EMA صاعد قوي")
        if ema9<ema21<ema50: sell+=2; rs.append("EMA هابط قوي")
        elif ema9>ema21: buy+=1; rs.append("EMA9>21")
        elif ema9<ema21: sell+=1; rs.append("EMA9<21")
        if macd>macd_s: buy+=1; rs.append("MACD صاعد")
        else: sell+=1; rs.append("MACD هابط")
        if price < bb_l*1.001: buy+=1; rs.append("عند Bollinger سفلي")
        if price > bb_u*0.999: sell+=1; rs.append("عند Bollinger علوي")

        if buy>=4 and buy>sell*1.5:
            sig="CALL قوي ⬆️⬆️"; conf=min(95,65+buy*5)
        elif sell>=4 and sell>buy*1.5:
            sig="PUT قوي ⬇️⬇️"; conf=min(95,65+sell*5)
        elif buy>sell:
            sig="CALL ⬆️"; conf=60+(buy-sell)*5
        elif sell>buy:
            sig="PUT ⬇️"; conf=60+(sell-buy)*5
        else:
            sig="انتظار ⏸️"; conf=50

        txt = "\n".join([f"• {x}" for x in rs[:5]])
        await update.message.reply_text(
            f"📊 {pair}\n💵 {price:.5f}\n📈 {sig}\n💪 {conf}%\n"
            f"RSI:{rsi:.1f} Stoch:{stoch:.1f}\nEMA {ema9:.5f}/{ema21:.5f}/{ema50:.5f}\n"
            f"MACD {macd:.4f}\nBB {bb_l:.5f}-{bb_u:.5f}\n\n{txt}\n\n⏰ 3-5 دقايق"
        )
    except Exception as e:
        await update.message.reply_text(f"خطأ: {e}")

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("NO TOKEN")
    else:
        print("Bot starting...")
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("pairs", pairs))
        app.add_handler(CommandHandler("signal", signal))
        app.run_polling()