import requests
import os
import time
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

        update.message.reply_text("Scraping started... (PRO MODE 🔥)")

        with open("keywords.txt", "r", encoding="utf-8") as f:
            keywords = [line.strip() for line in f if line.strip()]

        numbers = []

        for keyword in keywords:

            # 🔍 STEP 1: SEARCH
            search_url = f"https://api.scrapingdog.com/google_maps?api_key={API_KEY}&query={keyword}"

            try:
                res = requests.get(search_url)
                data = res.json()
            except:
                continue

            results = data.get("data") or []

            for place in results:

                place_id = place.get("place_id")

                if not place_id:
                    continue

                # 🔥 STEP 2: DETAIL (MAIN MAGIC)
                detail_url = f"https://api.scrapingdog.com/google_maps_details?api_key={API_KEY}&place_id={place_id}"

                try:
                    detail_res = requests.get(detail_url)
                    detail_data = detail_res.json()

                    phone = detail_data.get("phone")

                    if phone:
                        numbers.append(str(phone))

                except:
                    continue

                time.sleep(0.5)  # safe delay

        # remove duplicates
        numbers = list(set(numbers))

        if len(numbers) == 0:
            update.message.reply_text("No numbers found ❌")
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

print("PRO Bot running...")
updater.start_polling()
updater.idle()
