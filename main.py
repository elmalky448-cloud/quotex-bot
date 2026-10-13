from tradingview_ta import TA_Handler, Interval
import time, requests
from datetime import datetime

# ========== اعدادات تليجرام ==========
TOKEN = "حط توكن البوت هنا من @BotFather"
CHAT_ID = "حط الايدي بتاعك هنا"
# عشان تجيب الايدي ابعت رسالة لبوت @userinfobot

# ازواج Quotex كلها + الـ OTC
QUOTEX_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "EURJPY",
    "GBPJPY", "EURGBP", "USDCAD", "AUDJPY", "EURUSD_OTC",
    "GBPUSD_OTC", "EURJPY_OTC", "USDJPY_OTC", "BTCUSD", "BTCUSD_OTC"
]

EXCHANGE_MAP = {
    "EURUSD": ("FX:EURUSD", "FX"), "GBPUSD": ("FX:GBPUSD", "FX"),
    "EURUSD_OTC": ("FX:EURUSD", "FX"), # بنقرا نفس السعر الحقيقي
    "GBPUSD_OTC": ("FX:GBPUSD", "FX"),
    "BTCUSD": ("BINANCE:BTCUSDT", "BINANCE"),
    "BTCUSD_OTC": ("BINANCE:BTCUSDT", "BINANCE"),
}
# باقي الازواج هتتقرا من FX تلقائي

def check_pair(pair_name):
    try:
        symbol, exchange = EXCHANGE_MAP.get(pair_name, (f"FX:{pair_name.replace('_OTC','')}", "FX"))

        handler = TA_Handler(
            symbol=symbol,
            exchange=exchange,
            screener="forex" if "FX" in symbol or "BINANCE" not in symbol else "crypto",
            interval=Interval.INTERVAL_1_MINUTE,
            timeout=10
        )
        analysis = handler.get_analysis()
        ind = analysis.indicators
        osc = analysis.oscillators

        rsi = ind.get("RSI", 50)
        ema9 = ind.get("EMA9", 0)
        ema20 = ind.get("EMA20", 0)
        price = ind.get("close", 0)
        bb_lower = ind.get("BB.lower", 0)
        bb_upper = ind.get("BB.upper", 0)
        macd = ind.get("MACD.macd", 0)
        macd_signal = ind.get("MACD.signal", 0)

        # === استراتيجية البرو ===
        score = 0
        signal_type = None
        reasons = []

        # شروط CALL
        if price <= bb_lower * 1.002 and rsi < 32 and macd > macd_signal:
            signal_type = "CALL 🟢"
            score = 80 + (35 - rsi)
            reasons.append(f"RSI={rsi:.1f} تشبع بيع")
            reasons.append("لمس Bollinger سفلي")
            if price > ema9:
                score += 5
                reasons.append("فوق EMA9")

        # شروط PUT
        elif price >= bb_upper * 0.998 and rsi > 68 and macd < macd_signal:
            signal_type = "PUT 🔴"
            score = 80 + (rsi - 65)
            reasons.append(f"RSI={rsi:.1f} تشبع شراء")
            reasons.append("لمس Bollinger علوي")
            if price < ema9:
                score += 5
                reasons.append("تحت EMA9")

        if signal_type and score >= 78:
            return {
                "pair": pair_name,
                "type": signal_type,
                "score": min(95, score),
                "price": price,
                "reason": " | ".join(reasons),
                "rsi": rsi
            }
    except Exception as e:
        # print(f"Error {pair_name}: {e}")
        return None
    return None

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

print("🚀 بوت Quotex Pro شغال...")

last_sent = {}
while True:
    all_signals = []
    for p in QUOTEX_PAIRS:
        res = check_pair(p)
        if res:
            # ميبعتش نفس الزوج مرتين ورا بعض قبل 5 دقايق
            if p in last_sent and (datetime.now() - last_sent[p]).seconds < 300:
                continue
            all_signals.append(res)
        time.sleep(1) # عشان TradingView ميعملش بلوك

    if all_signals:
        best = sorted(all_signals, key=lambda x: x['score'], reverse=True)[0]
        msg = f"""🔥 *اشارة Quotex Pro*

💱 *الزوج:* `{best['pair']}`
🎯 *الاتجاه:* {best['type']} - دقيقة واحدة
💪 *القوة:* {best['score']:.0f}%
💵 *السعر:* {best['price']}

📊 *التحليل:* {best['reason']}

⏰ *ادخل من بداية الشمعة الجاية*
⚠️ *ادارة راس مال: 1% فقط*
"""
        send(msg)
        last_sent[best['pair']] = datetime.now()
        print(f"تم ارسال: {best['pair']} - {best['type']}")

    print(f"فحص الساعة {datetime.now().strftime('%H:%M:%S')} - مفيش اشارات قوية")
    time.sleep(60)
