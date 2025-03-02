from flask import Flask
from main import main

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == "__main__":
    # Start the bot in a background thread
    import threading
    threading.Thread(target=main).start()
    app.run(host="0.0.0.0", port=5000)
