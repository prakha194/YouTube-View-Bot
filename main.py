import time
import random
import requests
import subprocess
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")  # Your Telegram user ID for DM
WINDSCRIBE_USER = os.getenv("WINDSCRIBE_USER")
WINDSCRIBE_PASS = os.getenv("WINDSCRIBE_PASS")

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
    send_dm("✅ Bot has been started!")

# Stop bot command
def stop(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(f"⏸️ Bot is paused! No views will be sent until you use /start.")
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

# Function to watch Shorts video in browser
def watch_video(video_url):
    print(f"👀 Watching: {video_url}")
    
    # Setup Chrome browser
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in background
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get(video_url)
        time.sleep(random.randint(30, 90))  # Simulate human watch time
    except Exception as e:
        print("Error watching video:", e)
    finally:
        driver.quit()

# Auto-view function (Random 1-5 views per week)
def auto_view():
    videos = [
        "https://www.youtube.com/shorts/ABC123",  # Replace with real Shorts URLs
        "https://www.youtube.com/shorts/XYZ456"
    ]
    
    if not videos:
        print("No videos found!")
        return

    num_views = random.randint(1, 5)
    for _ in range(num_views):
        video = random.choice(videos)
        if change_ip():
            watch_video(video)
            print("✅ View sent!")
            time.sleep(random.randint(600, 1800))  # Delay before next view

# Handle /task command (Manual input)
def task(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("Submit Order", callback_data="submit_task")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("📌 Enter YouTube Shorts URL, Views & Date:", reply_markup=reply_markup)

# Handle manual order submission
def submit_task(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_input = query.message.text.split()
    if len(user_input) < 3:
        query.edit_message_text("❌ Invalid format! Please provide:\n\n📌 YouTube Shorts URL\n📌 Number of Views\n📌 Date")
        return
    
    video_url = user_input[0]
    num_views = int(user_input[1])
    order_date = user_input[2]

    if num_views > 5:
        query.edit_message_text("❌ Invalid number of views! Max allowed is 5.")
        return

    scheduled_tasks.append({"video": video_url, "views": num_views, "date": order_date})
    query.edit_message_text(f"✅ Order Confirmed:\n{video_url}\n📌 {num_views} Views\n📅 {order_date}")
    send_dm(f"📌 New Order Received:\n{video_url}\n👀 {num_views} Views\n📅 {order_date}")

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

# Handle /analytic command
def analytic(update: Update, context: CallbackContext):
    total_views = sum(task['views'] for task in scheduled_tasks)
    update.message.reply_text(f"📊 Total All-Time Views Sent: {total_views}")

# Handle /progress command
def progress(update: Update, context: CallbackContext):
    update.message.reply_text("⏳ Fetching real-time bot activity...")
    send_dm("⏳ Progress requested!")

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
    dp.add_handler(CommandHandler("analytic", analytic))
    dp.add_handler(CommandHandler("progress", progress))
    dp.add_handler(CommandHandler("report", report))

    updater.start_polling()
    updater.idle()

# Run bot & Flask server
if __name__ == '__main__':
    login_windscribe()
    Thread(target=telegram_bot).start()
    Thread(target=auto_view).start()
    app.run(host="0.0.0.0", port=8080)