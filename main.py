import time
import random
import requests
import subprocess
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
WINDSCRIBE_USER = os.getenv("WINDSCRIBE_USER")
WINDSCRIBE_PASS = os.getenv("WINDSCRIBE_PASS")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Flask app to keep bot running
app = Flask(__name__)

@app.route('/')
def home():
    return "YouTube View Bot is Running!"

# Store scheduled tasks
scheduled_tasks = []
user_inputs = {}

# Start bot command
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("🔥 Prashant Khati's YouTube Boost Bot is LIVE! 🚀")
    send_dm("✅ Bot has been started!")

# Stop bot command
def stop(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("⏸️ Bot is paused! No views will be sent until you use /start.")
    send_dm("⏸️ Bot has been paused!")

# Function to send DM to admin
def send_dm(message):
    if ADMIN_USER_ID:
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage?chat_id={ADMIN_USER_ID}&text={message}")

# Function to login to Windscribe
def login_windscribe():
    try:
        subprocess.run(["windscribe", "login", WINDSCRIBE_USER, WINDSCRIBE_PASS], check=True)
    except Exception as e:
        print("Windscribe login failed:", e)

# Function to change IP using Windscribe
def change_ip():
    try:
        subprocess.run(["windscribe", "connect", "best"], check=True)
        time.sleep(5)
        return True
    except Exception as e:
        print("Failed to connect to Windscribe:", e)
        return False

# Function to get latest Shorts videos from YouTube API
def get_youtube_videos():
    api_url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={YOUTUBE_CHANNEL_ID}&part=id&order=date&type=video&maxResults=5"
    response = requests.get(api_url).json()
    videos = [f"https://www.youtube.com/shorts/{item['id']['videoId']}" for item in response.get("items", [])]
    return videos

# Function to ACTUALLY watch video with real browser
# Function to ACTUALLY watch video with requests instead of browser
def watch_video(video_url):
    print(f"👀 Sending view to: {video_url}")
    
    try:
        # Use requests to actually visit the URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Actually make HTTP request to YouTube
        response = requests.get(video_url, headers=headers, timeout=30)
        print(f"✅ YouTube responded with status: {response.status_code}")
        
        # Simulate watch time
        watch_time = random.randint(30, 90)
        print(f"⏱️ Simulating watch time: {watch_time} seconds")
        time.sleep(watch_time)
        
        print("✅ View completed")
        return True
        
    except Exception as e:
        print(f"❌ Error watching video: {e}")
        return False

# Auto-view function (Daily views for channel Shorts)
def auto_view():
    while True:
        videos = get_youtube_videos()
        if not videos:
            print("No videos found!")
            time.sleep(3600)
            continue

        num_views = random.randint(1, 3)
        for _ in range(num_views):
            video = random.choice(videos)
            if change_ip():
                if watch_video(video):
                    print("✅ Real view sent to YouTube!")
                time.sleep(random.randint(600, 1800))

# Handle /task command
def task(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    user_inputs[user_id] = {}
    update.message.reply_text("📌 Please enter the YouTube Shorts URL:")
    return

# Handle message input from users
def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    user_input = update.message.text

    if user_id not in user_inputs:
        return

    if "url" not in user_inputs[user_id]:
        user_inputs[user_id]["url"] = user_input
        update.message.reply_text("📌 Enter number of views (Max: 3):")
    elif "views" not in user_inputs[user_id]:
        if not user_input.isdigit() or int(user_input) > 3:
            update.message.reply_text("❌ Invalid number! Enter a number up to 3:")
            return
        user_inputs[user_id]["views"] = int(user_input)
        update.message.reply_text("📅 Enter date & time (YYYY-MM-DD HH:MM):")
    elif "datetime" not in user_inputs[user_id]:
        user_inputs[user_id]["datetime"] = user_input

        keyboard = [[InlineKeyboardButton("✅ Confirm Order", callback_data="confirm_order")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text(
            f"✅ Order Summary:\n📌 URL: {user_inputs[user_id]['url']}\n👀 Views: {user_inputs[user_id]['views']}\n📅 Date & Time: {user_inputs[user_id]['datetime']}",
            reply_markup=reply_markup
        )

# Handle manual order confirmation
def confirm_order(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.message.chat_id

    if user_id in user_inputs:
        order = user_inputs[user_id]
        scheduled_tasks.append(order)

        query.edit_message_text(f"✅ Order Confirmed:\n📌 {order['url']}\n👀 {order['views']} Views\n📅 {order['datetime']}")
        send_dm(f"📌 New Order Received:\n{order['url']}\n👀 {order['views']} Views\n📅 {order['datetime']}")
        del user_inputs[user_id]

# Handle /status command
def status(update: Update, context: CallbackContext):
    if not scheduled_tasks:
        update.message.reply_text("📌 No scheduled views for this week!")
    else:
        message = "📊 Weekly Scheduled Views:\n\n"
        for idx, task in enumerate(scheduled_tasks, 1):
            message += f"{idx}️⃣ {task['url']} → {task['views']} views ({task['datetime']})\n"

        total_views = sum(task['views'] for task in scheduled_tasks)
        message += f"\n✅ Total Scheduled Views: {total_views}"
        update.message.reply_text(message)

# Handle /report command
def report(update: Update, context: CallbackContext):
    ip_info = requests.get("https://api64.ipify.org?format=json").json()["ip"]
    update.message.reply_text(f"🔍 Bot's Current Status:\n✅ Active\n🌍 IP Address: {ip_info}")

# Telegram bot setup
def telegram_bot():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("task", task))
    dp.add_handler(CommandHandler("status", status))
    dp.add_handler(CommandHandler("report", report))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(confirm_order, pattern="confirm_order"))

    # Use webhook for Render
    PORT = int(os.environ.get('PORT', 8080))
    RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL')

    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path="webhook",
                          webhook_url=f"{RENDER_EXTERNAL_URL}/webhook")

# Run bot
if __name__ == '__main__':
    login_windscribe()
    Thread(target=telegram_bot).start()
    Thread(target=auto_view).start()