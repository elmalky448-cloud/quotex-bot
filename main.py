import os, threading, time
from fastapi import FastAPI
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN")
app = FastAPI()
bot = telebot.TeleBot(BOT_TOKEN, threaded=False) if BOT_TOKEN else None

@app.get("/")
def home():
    return {"status": "QUOTEX PRO FINAL - REAL MARKET"}

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, """✅ Quotex PRO - النسخة النهائية

تحليل سوق حقيقي 100% - مفيش عشوائي

الأوامر:
📊 /signal EURUSD - يورو دولار
📊 /signal GBPUSD - باوند
📊 /signal USDJPY
📊 /signal BTCUSD - بتكوين
📊 /signal GOLD

⚠️ ممنوع OTC - دي اسواق وهمية

💡 الفريم: 5 دقايق - دخول 3-5 دقايق
🕐 اشتغل من 10 صباحا لـ 6 مساء بتوقيت القاهرة
""")

@bot.message_handler(commands=['pairs'])
def pairs(m):
    bot.reply_to(m, "الأزواج الحقيقية فقط:\nEURUSD\nGBPUSD\nUSDJPY\nAUDUSD\nUSDCAD\nBTCUSD\nGOLD")

@bot.message_handler(commands=['signal'])
def signal(m):
    parts = m.text.split()
    raw_pair = parts[1].upper() if len(parts) > 1 else "EURUSD"

    if "OTC" in raw_pair:
        bot.reply_to(m, f"❌ {raw_pair} سوق وهمي من Quotex\nمش هعرف احلله تحليل حقيقي\n\nجرب:\n/signal EURUSD\nده سوق حقيقي 100%")
        return

    pair = raw_pair
    try:
        bot.reply_to(m, f"🔍 بحلل {pair} من السوق الحقيقي (5m)...")

        import yfinance as yf
        import pandas as pd

        symbol_map = {
            "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD