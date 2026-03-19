import requests
import os
import json
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

        update.message.reply_text("Fetching raw data...")

        with open("keywords.txt", "r", encoding="utf-8") as f:
            keywords = [line.strip() for line in f if line.strip()]

        all_data = []

        for keyword in keywords:
            url = "https://api.scrapingdog.com/google_maps"

            params = {
                "api_key": API_KEY,
                "query": keyword,
                "language": "en"
            }

            try:
                res = requests.get(url, params=params)
                data = res.json()

                # 🔥 pura response store
                all_data.append({
                    "keyword": keyword,
                    "response": data
                })

            except Exception as e:
                all_data.append({
                    "keyword": keyword,
                    "error": str(e)
                })

        # save as txt (json format)
        with open("output.txt", "w", encoding="utf-8") as f:
            for item in all_data:
                f.write(json.dumps(item, indent=2))
                f.write("\n\n")

        # send file
        f = open("output.txt", "rb")
        update.message.reply_document(document=f)
        f.close()

    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")


updater = Updater(BOT_TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(MessageHandler(Filters.document, handle_file))

print("Raw Data Bot Running...")
updater.start_polling()
updater.idle()
