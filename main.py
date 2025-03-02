import time
import random
import requests
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext
from config import TELEGRAM_BOT_TOKEN, YOUTUBE_CHANNEL_ID, WINDSCRIBE_USERNAME, WINDSCRIBE_PASSWORD, MAX_VIEWS, USE_FREE_PROXIES

# Store scheduled views
scheduled_tasks = []

# Start bot command
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(f"🔥 Prashant Khati's YouTube Boost Bot is LIVE! 🚀")

# Stop bot command
def stop(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(f"⏸️ Bot is paused! No views will be sent until you use /start.")

# Function to rotate IP using Windscribe
def change_ip():
    try:
        subprocess.run(["windscribe", "connect", "best"], check=True)
        time.sleep(5)
        return True
    except Exception as e:
        print("Failed to connect to Windscribe:", e)
        return False

# Function to get video list from YouTube API
def get_youtube_videos():
    api_url = f"https://www.googleapis.com/youtube/v3/search?key=YOUR_YOUTUBE_API_KEY&channelId={YOUTUBE_CHANNEL_ID}&part=id&order=date&type=video"
    response = requests.get(api_url).json()
    
    videos = [f"https://www.youtube.com/watch?v={item['id']['videoId']}" for item in response.get("items", [])]
    return videos

# Function to simulate a view
def watch_video(video_url):
    print(f"👀 Watching: {video_url}")
    time.sleep(random.randint(30, 90))  # Simulate human watch time

# Auto-view function
def auto_view():
    videos = get_youtube_videos()
    if not videos:
        print("No videos found!")
        return
    
    for video in videos:
        if change_ip():
            watch_video(video)
            print("✅ View sent!")
            time.sleep(random.randint(600, 1800))  # Delay before next view

# Handle /task command (Manual input)
def task(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("Submit Order", callback_data="submit_task")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("📌 Enter YouTube Video URL, Views & Date:", reply_markup=reply_markup)

# Handle /status command
def status(update: Update, context: CallbackContext):
    if not scheduled_tasks:
        update.message.reply_text("No scheduled views!")
    else:
        message = "📊 Weekly Scheduled Views:\n"
        for task in scheduled_tasks:
            message += f"📺 {task['video']} → {task['views']} views ({task['date']})\n"
        update.message.reply_text(message)

# Set up the Telegram bot
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("task", task))
    dp.add_handler(CommandHandler("status", status))

    updater.start_polling()
    updater.idle()

# Run the bot
if __name__ == '__main__':
    main()
