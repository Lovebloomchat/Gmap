import requests
import os
from telegram.ext import Updater, MessageHandler, Filters

API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

def handle_file(update, context):
    file = update.message.document.get_file()
    file.download("keywords.txt")

    update.message.reply_text("Scraping started...")

    with open("keywords.txt", "r") as f:
        keywords = f.read().splitlines()

    numbers = []

    for keyword in keywords:
        keyword = keyword.strip()
        if not keyword:
            continue

        url = f"https://api.scrapingdog.com/google_maps?api_key={API_KEY}&query={keyword}"
        res = requests.get(url).json()

        for place in res.get("data", []):
            phone = place.get("phone")
            if phone:
                numbers.append(phone)

    numbers = list(set(numbers))

    with open("numbers.txt", "w") as f:
        for num in numbers:
            f.write(num + "\n")

    update.message.reply_document(document=open("numbers.txt", "rb"))

updater = Updater(BOT_TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(MessageHandler(Filters.document, handle_file))

updater.start_polling()
updater.idle()
