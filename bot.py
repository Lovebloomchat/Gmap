import requests
import os
from telegram.ext import Updater, MessageHandler, Filters

API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

def handle_file(update, context):
    try:
        # file download
        file = update.message.document.get_file()
        file.download("keywords.txt")

        update.message.reply_text("Scraping started...")

        # read keywords
        with open("keywords.txt", "r") as f:
            keywords = f.read().splitlines()

        numbers = []

        for keyword in keywords:
            keyword = keyword.strip()
            if not keyword:
                continue

            url = f"https://api.scrapingdog.com/google_maps?api_key={API_KEY}&query={keyword}"

            try:
                res = requests.get(url)
                data = res.json()
            except:
                continue

            for place in data.get("data", []):
                phone = place.get("phone")
                if phone:
                    numbers.append(phone)

        # remove duplicates
        numbers = list(set(numbers))

        # save file
        with open("numbers.txt", "w") as f:
            for num in numbers:
                f.write(num + "\n")

        # send file (FIXED)
        f = open("numbers.txt", "rb")
        update.message.reply_document(document=f)
        f.close()

    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")


# bot start
updater = Updater(BOT_TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(MessageHandler(Filters.document, handle_file))

print("Bot is running...")
updater.start_polling()
updater.idle()
