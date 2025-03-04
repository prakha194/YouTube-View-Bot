import time
import random
import os
import requests
import subprocess
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext
from config import TELEGRAM_BOT_TOKEN, YOUTUBE_CHANNEL_ID

# Flask app to keep bot running
app = Flask(__name__)

@app.route('/')
def home():
    return "YouTube View Bot is Running!"

# Store scheduled views
scheduled_tasks = []

# Start bot command
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(f"🔥 Prashant Khati's YouTube Boost Bot is LIVE! 🚀")

# Stop bot command
def stop(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(f"⏸️ Bot is paused! No views will be sent until you use /start.")

# Windscribe login & IP rotation
def windscribe_login():
    username = os.getenv("WINDSCRIBE_USER")
    password = os.getenv("WINDSCRIBE_PASS")
    
    if not username or not password:
        print("❌ Windscribe credentials missing!")
        return False

    try:
        subprocess.run(["windscribe", "login", username, password], check=True)
        print("✅ Windscribe login successful!")
        return True
    except Exception as e:
        print(f"❌ Windscribe login failed: {e}")
        return False

def change_ip():
    if not windscribe_login():
        return False
    
    try:
        subprocess.run(["windscribe", "connect", "best"], check=True)
        time.sleep(5)
        return True
    except Exception as e:
        print("❌ Failed to connect to Windscribe:", e)
        return False

# Get video list from YouTube API
def get_youtube_videos():
    api_url = f"https://www.googleapis.com/youtube/v3/search?key=YOUR_YOUTUBE_API_KEY&channelId={YOUTUBE_CHANNEL_ID}&part=id&order=date&type=video"
    response = requests.get(api_url).json()

    videos = [f"https://www.youtube.com/watch?v={item['id']['videoId']}" for item in response.get("items", [])]
    return videos

# Simulate a view
def watch_video(video_url):
    print(f"👀 Watching: {video_url}")
    time.sleep(random.randint(30, 90))  # Simulate human watch time

# Auto-view function (max 5 views/week)
def auto_view():
    videos = get_youtube_videos()
    if not videos:
        print("No videos found!")
        return

    weekly_views = random.randint(1, 5)
    for _ in range(weekly_views):
        video = random.choice(videos)
        if change_ip():
            watch_video(video)
            print(f"✅ View sent to {video}")
            time.sleep(random.randint(600, 1800))  # Delay before next view

# Handle /task command (Manual input)
def task(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("Submit Order", callback_data="submit_task")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("📌 Enter YouTube Video URL, Views & Date:", reply_markup=reply_markup)

# Handle /status command
def status(update: Update, context: CallbackContext):
    if not scheduled_tasks:
        update.message.reply_text("📌 No scheduled views for this week!")
    else:
        message = "📊 Weekly Scheduled Views:\n\n"
        for idx, task in enumerate(scheduled_tasks, 1):
            message += f"{idx}️⃣ {task['video']} → {task['views']} views ({task['date']})\n"

        total_views = sum(task['views'] for task in scheduled_tasks)
        message += f"\n✅ Total Scheduled Views: {total_views}"

        update.message.reply_text(message)

# Telegram bot setup
def telegram_bot():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("task", task))
    dp.add_handler(CommandHandler("status", status))

    updater.start_polling()
    updater.idle()

# Run bot & Flask server
if __name__ == '__main__':
    Thread(target=telegram_bot).start()
    Thread(target=auto_view).start()  # Auto-viewing starts in the background
    app.run(host="0.0.0.0", port=8080)