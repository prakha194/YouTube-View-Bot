import time
import random
import requests
import subprocess
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import os

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")  # Your Telegram user ID for DM
WINDSCRIBE_USER = os.getenv("WINDSCRIBE_USER")
WINDSCRIBE_PASS = os.getenv("WINDSCRIBE_PASS")

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
    api_url = f"https://www.googleapis.com/youtube/v3/search?key={os.getenv('YOUTUBE_API_KEY')}&channelId={YOUTUBE_CHANNEL_ID}&part=id&order=date&type=video&maxResults=5"
    response = requests.get(api_url).json()
    videos = [f"https://www.youtube.com/shorts/{item['id']['videoId']}" for item in response.get("items", [])]
    return videos

# Function to simulate a view
def watch_video(video_url):
    print(f"👀 Watching: {video_url}")
    time.sleep(random.randint(30, 90))  # Simulate human watch time

# Auto-view function (Daily views for channel Shorts)
def auto_view():
    while True:
        videos = get_youtube_videos()
        if not videos:
            print("No videos found!")
            time.sleep(3600)  # Wait 1 hour before retrying
            continue

        num_views = random.randint(1, 5)
        for _ in range(num_views):
            video = random.choice(videos)
            if change_ip():
                watch_video(video)
                print("✅ View sent!")
                time.sleep(random.randint(600, 1800))  # Delay before next view

# Handle /task command (Step-by-step input)
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
        update.message.reply_text("📌 Enter number of views (Max: 5):")
    elif "views" not in user_inputs[user_id]:
        if not user_input.isdigit() or int(user_input) > 5:
            update.message.reply_text("❌ Invalid number! Enter a number up to 5:")
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
        del user_inputs[user_id]  # Clear user data after confirmation

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

    updater.start_polling()
    updater.idle()

# Run bot & Flask server
if __name__ == '__main__':
    login_windscribe()
    Thread(target=telegram_bot).start()
    Thread(target=auto_view).start()
    app.run(host="0.0.0.0", port=8080)