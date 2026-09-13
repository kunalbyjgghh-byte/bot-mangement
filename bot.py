import telebot
import requests
import time
import threading
import os
import socketserver
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler

# Bot Token & Config (@Secondoo_bot / Bot 1)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8901542723:AAFd54ZpaMc9DyOdqEKp6KFsEXlFMzgygYU")
bot = telebot.TeleBot(BOT_TOKEN)

API_KEY = "e162df9b7dce5201f22c0decd4d4dff931c9904c708e1342b9da9b086e32b1ac"
API_URL = "https://yoyomedia.com/api/v2"

SERVICE_VIEWS = 4480
SERVICE_LIKES = 4731

ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

campaign_running = False
stop_campaign_flag = False
current_campaign_info = {}

# Views & Likes Quantities for 8 Steps
STEPS_DATA = [
    {"views": 117, "likes": 0},   # Step 1
    {"views": 348, "likes": 0},   # Step 2
    {"views": 765, "likes": 0},   # Step 3
    {"views": 1630, "likes": 10}, # Step 4
    {"views": 2404, "likes": 12}, # Step 5
    {"views": 2736, "likes": 15}, # Step 6
    {"views": 2896, "likes": 16}, # Step 7
    {"views": 3003, "likes": 17}, # Step 8
]

def check_admin(message):
    global ADMIN_ID
    if ADMIN_ID == 0:
        ADMIN_ID = message.chat.id
    return message.chat.id == ADMIN_ID

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

def get_balance():
    payload = {"key": API_KEY, "action": "balance"}
    try:
        res = requests.post(API_URL, data=payload)
        data = res.json()
        if "balance" in data:
            usd_bal = float(data['balance'])
            usd_to_inr_rate = 83.50  # 1 USD = ~83.50 INR
            inr_bal = usd_bal * usd_to_inr_rate
            
            return (
                f"💵 <b>Panel Balance:</b>\n"
                f"🇮🇳 <b>₹{inr_bal:.2f} INR</b>\n"
                f"🇺🇸 <code>${usd_bal:.2f} USD</code>"
            )
        else:
            return "❌ Unable to fetch balance."
    except Exception as e:
        return f"❌ Error fetching balance: {e}"

def get_ist_now():
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

def smart_sleep(seconds):
    global stop_campaign_flag
    for _ in range(int(seconds * 2)):
        if stop_campaign_flag:
            break
        time.sleep(0.5)

def run_campaign(chat_id, link, start_time_str, start_step):
    global campaign_running, stop_campaign_flag, current_campaign_info
    campaign_running = True
    stop_campaign_flag = False
    
    now = get_ist_now()
    
    # Time Parsing
    if start_time_str:
        try:
            sh, sm = map(int, start_time_str.split(":"))
            start_dt = now.replace(hour=sh, minute=sm, second=0, microsecond=0)
            if start_dt < now and (now - start_dt).total_seconds() > 300:
                start_dt = start_dt + timedelta(days=1)
        except Exception:
            start_dt = now
    else:
        start_dt = now

    steps_to_run = STEPS_DATA[start_step-1:]

    current_campaign_info = {
        "link": link,
        "start_time": start_dt.strftime('%I:%M %p'),
        "completed_steps": start_step - 1,
        "total_steps": 8
    }

    msg_start = (
        f"🚀 <b>Campaign Scheduled!</b>\n"
        f"🔗 <b>Link:</b> {link}\n"
        f"⏰ <b>Start Time:</b> <code>{start_dt.strftime('%I:%M %p')} IST</code>\n"
        f"🔢 <b>Starting from Batch/Step:</b> <code>{start_step}</code>"
    )
    bot.send_message(chat_id, msg_start, parse_mode="HTML")
    
    for relative_idx, step in enumerate(steps_to_run):
        if stop_campaign_flag:
            break
            
        actual_step_num = start_step + relative_idx
        target_dt = start_dt + timedelta(hours=relative_idx)
        target_time_str = target_dt.strftime("%I:%M %p")
        
        current_campaign_info["completed_steps"] = actual_step_num - 1
        current_campaign_info["next_step_time"] = target_time_str
        
        v_qty = step["views"]
        l_qty = step["likes"]
        
        while True:
            if stop_campaign_flag:
                break
                
            current_ist = get_ist_now()
            if current_ist >= target_dt:
                msg = f"⏰ <b>Batch/Step {actual_step_num}/8 ({target_time_str} IST)</b>\n"
                
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
                        
                bot.send_message(chat_id, msg, parse_mode="HTML")
                smart_sleep(5)
                break
            else:
                smart_sleep(5)
                
    if stop_campaign_flag:
        bot.send_message(chat_id, "🛑 <b>Campaign Stopped Successfully!</b>", parse_mode="HTML")
    else:
        bot.send_message(chat_id, "🎉 <b>Full Campaign Successfully Completed!</b>", parse_mode="HTML")
        
    campaign_running = False

# --- BOT COMMAND HANDLERS ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not check_admin(message):
        bot.reply_to(message, "⛔ Access Denied! You are not authorized.")
        return
        
    welcome_txt = (
        "👋 <b>Welcome Boss! Campaign Bot Control Panel</b>\n\n"
        "📌 <b>Available Commands:</b>\n"
        "🔹 <code>/run &lt;link&gt; &lt;time&gt; &lt;step&gt;</code> - Start campaign\n"
        "   <i>Example:</i> <code>/run https://reel_link 20:30 3</code>\n\n"
        "🔹 <code>/balance</code> - Check SMM Panel Balance in INR (₹)\n"
        "🔹 <code>/status</code> - Check Running Campaign Status\n"
        "🔹 <code>/stop</code> - Cancel/Stop Active Campaign"
    )
    bot.reply_to(message, welcome_txt, parse_mode="HTML")

@bot.message_handler(commands=['balance'])
def handle_balance(message):
    if not check_admin(message):
        return
    bal_msg = get_balance()
    bot.reply_to(message, bal_msg, parse_mode="HTML")

@bot.message_handler(commands=['status'])
def handle_status(message):
    if not check_admin(message):
        return
    if campaign_running:
        info = (
            f"📊 <b>Active Campaign Status:</b>\n\n"
            f"🔗 <b>Link:</b> {current_campaign_info.get('link')}\n"
            f"📈 <b>Completed Steps:</b> {current_campaign_info.get('completed_steps')}/8\n"
            f"⏰ <b>Next Step Time:</b> {current_campaign_info.get('next_step_time', 'Executing now')}"
        )
    else:
        info = "ℹ️ No campaign is currently running."
    bot.reply_to(message, info, parse_mode="HTML")

@bot.message_handler(commands=['stop'])
def handle_stop(message):
    global stop_campaign_flag, campaign_running
    if not check_admin(message):
        return
    if campaign_running:
        stop_campaign_flag = True
        bot.reply_to(message, "🛑 <b>Stopping campaign immediately...</b>", parse_mode="HTML")
    else:
        bot.reply_to(message, "ℹ️ No active campaign to stop.")

@bot.message_handler(commands=['run'])
def handle_run(message):
    if not check_admin(message):
        return
    global campaign_running
    if campaign_running:
        bot.reply_to(message, "⚠️ Pehle se ek campaign chal rahi hai! Use `/stop` to cancel it first.")
        return
        
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ Link missing!\nUsage: `/run <link> <time> <step>`")
        return
    
    link = parts[1]
    start_time_str = parts[2] if len(parts) >= 3 else None
    
    start_step = 1
    if len(parts) >= 4:
        try:
            start_step = int(parts[3])
            if start_step < 1 or start_step > 8:
                start_step = 1
        except ValueError:
            start_step = 1
    
    threading.Thread(target=run_campaign, args=(message.chat.id, link, start_time_str, start_step)).start()

# --- FIXED DUMMY SERVER FOR RENDER ---
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", port), DummyServer) as httpd:
        httpd.serve_forever()

threading.Thread(target=keep_alive, daemon=True).start()
# -------------------------------------

print("🤖 Telegram Bot is Active!")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Connection lost: {e}. Reconnecting in 5 seconds...")
        time.sleep(5)
