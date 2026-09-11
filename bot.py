import telebot
import requests
import time
import threading
import os
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

# Naya Bot Token
BOT_TOKEN = "8901542723:AAEhjajWnzyDXq03RPA28EZfi7lHbC-RYxo"
bot = telebot.TeleBot(BOT_TOKEN)

API_KEY = "e162df9b7dce5201f22c0decd4d4dff931c9904c708e1342b9da9b086e32b1ac"
API_URL = "https://yoyomedia.com/api/v2"

SERVICE_VIEWS = 4480
SERVICE_LIKES = 4731

# Exact Sheet Schedule (3:00 PM se start)
SCHEDULE = [
    {"time": "15:00", "views": 117, "likes": 0},   # 1st hour
    {"time": "16:00", "views": 348, "likes": 0},   # 2nd hour
    {"time": "17:00", "views": 765, "likes": 0},   # 3rd hour
    {"time": "18:00", "views": 1630, "likes": 10}, # 4th hour
    {"time": "19:00", "views": 2404, "likes": 12}, # 5th hour
    {"time": "20:00", "views": 2736, "likes": 15}, # 6th hour
    {"time": "21:00", "views": 2896, "likes": 16}, # 7th hour
    {"time": "22:00", "views": 3003, "likes": 17}, # 8th hour
]

def place_order(service_id, link, quantity):
    if quantity <= 0:
        return None
    payload = {
        "key": API_KEY, "action": "add", 
        "service": service_id, "link": link, "quantity": quantity
    }
    try:
        res = requests.post(API_URL, data=payload)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

def run_campaign(chat_id, link):
    bot.send_message(chat_id, "🚀 *Campaign Queued!*\nBot time ka wait kar raha hai aur theek 3:00 PM se orders lagana shuru karega.", parse_mode="Markdown")
    
    for step in SCHEDULE:
        target_time = step["time"]
        v_qty = step["views"]
        l_qty = step["likes"]
        
        while True:
            ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
            current_time = ist_now.strftime("%H:%M")
            
            if current_time >= target_time:
                msg = f"⏰ *Time Slot: {target_time} (IST)*\n"
                
                if v_qty > 0:
                    v_res = place_order(SERVICE_VIEWS, link, v_qty)
                    if v_res and "order" in v_res:
                        msg += f"👁️ Views (+{v_qty}): ✅ [ID: {v_res['order']}]\n"
                    else:
                        msg += f"👁️ Views (+{v_qty}): ❌ Failed\n"
                        
                if l_qty > 0:
                    l_res = place_order(SERVICE_LIKES, link, l_qty)
                    if l_res and "order" in l_res:
                        msg += f"❤️ Likes (+{l_qty}): ✅ [ID: {l_res['order']}]"
                    else:
                        msg += f"❤️ Likes (+{l_qty}): ❌ Panel Error"
                        
                bot.send_message(chat_id, msg, parse_mode="Markdown")
                time.sleep(60) 
                break
            else:
                time.sleep(30) 
            
    bot.send_message(chat_id, "🎉 *Full Campaign Successfully Completed!*", parse_mode="Markdown")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Welcome Bot!\nOrder lagane ke liye aise bhejein:\n\n`/run <link>`", parse_mode="Markdown")

@bot.message_handler(commands=['run'])
def handle_run(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ Link missing! Aise bhejein:\n`/run https://www.instagram.com/reel/xyz/`", parse_mode="Markdown")
        return
    link = parts[1]
    threading.Thread(target=run_campaign, args=(message.chat.id, link)).start()

# --- DUMMY SERVER FOR RENDER WEB SERVICE ---
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), DummyServer)
    server.serve_forever()

threading.Thread(target=keep_alive, daemon=True).start()
# -------------------------------------------

print("🤖 Telegram Bot is Active!")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Connection lost: {e}. Reconnecting in 5 seconds...")
        time.sleep(5)
