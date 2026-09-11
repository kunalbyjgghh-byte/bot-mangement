import telebot
import requests
import time
import threading
import os
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

BOT_TOKEN = "7880836150:AAGfi6EYwQXen_4ezbkj9l2mJnbZB-G-Yng"
bot = telebot.TeleBot(BOT_TOKEN)

API_KEY = "e162df9b7dce5201f22c0decd4d4dff931c9904c708e1342b9da9b086e32b1ac"
API_URL = "https://yoyomedia.com/api/v2"

SERVICE_VIEWS = 4480
SERVICE_LIKES = 4731

# 11:40 AM se shuru hone wala schedule
SCHEDULE = [
    {"time": "11:40", "views": 117, "likes": 0},
    {"time": "12:40", "views": 231, "likes": 0},
    {"time": "13:40", "views": 417, "likes": 0},
    {"time": "14:40", "views": 865, "likes": 10}, # 2:40 PM
    {"time": "15:40", "views": 774, "likes": 12}, # 3:40 PM
    {"time": "16:40", "views": 332, "likes": 15}, # 4:40 PM
    {"time": "17:40", "views": 160, "likes": 16}, # 5:40 PM
    {"time": "18:40", "views": 107, "likes": 17}, # 6:40 PM
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
    bot.send_message(chat_id, "🚀 *11:40 AM Campaign Started!*\nBot time ke hisaab se orders place karega.", parse_mode="Markdown")
    
    for step in SCHEDULE:
        target_time = step["time"]
        v_qty = step["views"]
        l_qty = step["likes"]
        
        while True:
            ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
            current_time = ist_now.strftime("%H:%M")
            
            if current_time == target_time:
                msg = f"⏰ *Time: {target_time} (IST)*\n"
                
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
    bot.reply_to(message, "👋 Welcome to Quickheal Bot!\nOrder lagane ke liye aise bhejein:\n\n`/run <link>`", parse_mode="Markdown")

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
