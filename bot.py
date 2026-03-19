import requests
import os
from telegram.ext import Updater, MessageHandler, Filters

API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

def handle_file(update, context):
    try:
        document = update.message.document

        if not document.file_name.endswith(".txt"):
            update.message.reply_text("Only .txt file allowed")
            return

        file = document.get_file()
        file.download("keywords.txt")

        update.message.reply_text("Extracting numbers...")

        with open("keywords.txt", "r", encoding="utf-8") as f:
            keywords = [line.strip() for line in f if line.strip()]

        numbers = []

        for keyword in keywords:
            url = "https://api.scrapingdog.com/google_maps"

            params = {
                "api_key": API_KEY,
                "query": keyword
            }

            res = requests.get(url, params=params)
            data = res.json()

            # 🔥 MAIN LINE (IMPORTANT)
            results = data.get("search_results") or data.get("data") or []

            for place in results:
                phone = place.get("phone")

                if phone:
                    numbers.append(phone)

        # remove duplicates
        numbers = list(set(numbers))

        if not numbers:
            update.message.reply_text("Koi number nahi mila ❌")
            return

        with open("numbers.txt", "w") as f:
            for num in numbers:
                f.write(num + "\n")

        f = open("numbers.txt", "rb")
        update.message.reply_document(document=f)
        f.close()

    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")


updater = Updater(BOT_TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(MessageHandler(Filters.document, handle_file))

print("Bot running...")
updater.start_polling()
updater.idle()
