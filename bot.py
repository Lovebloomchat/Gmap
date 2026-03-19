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

        # download file
        file = document.get_file()
        file.download("keywords.txt")

        update.message.reply_text("Scraping started...")

        # read keywords
        with open("keywords.txt", "r", encoding="utf-8") as f:
            keywords = [line.strip() for line in f if line.strip()]

        results_list = []

        for keyword in keywords:
            url = "https://api.scrapingdog.com/google_maps"

            params = {
                "api_key": API_KEY,
                "query": keyword
            }

            try:
                res = requests.get(url, params=params)
                data = res.json()

                # 🔥 handle multiple formats
                results = data.get("search_results") or data.get("data") or []

                for place in results:
                    phone = place.get("phone")
                    name = place.get("title")

                    if phone and name:
                        results_list.append(f"{phone} : {name}")

            except:
                continue

        # remove duplicates
        results_list = list(set(results_list))

        if not results_list:
            update.message.reply_text("Koi data nahi mila ❌")
            return

        # save file
        with open("output.txt", "w", encoding="utf-8") as f:
            for item in results_list:
                f.write(item + "\n")

        # send file
        f = open("output.txt", "rb")
        update.message.reply_document(document=f)
        f.close()

    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")


# start bot
updater = Updater(BOT_TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(MessageHandler(Filters.document, handle_file))

print("Bot running...")
updater.start_polling()
updater.idle()
