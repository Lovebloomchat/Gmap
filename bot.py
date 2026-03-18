import requests
import os
from telegram.ext import Updater, MessageHandler, Filters

API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

def handle_file(update, context):
    try:
        document = update.message.document

        # check file type
        if not document.file_name.endswith(".txt"):
            update.message.reply_text("Please upload only .txt file")
            return

        # download file
        file = document.get_file()
        file.download("keywords.txt")

        update.message.reply_text("File received. Reading...")

        # read keywords
        with open("keywords.txt", "r", encoding="utf-8") as f:
            keywords = [line.strip() for line in f if line.strip()]

        if len(keywords) == 0:
            update.message.reply_text("File empty hai ❌")
            return

        update.message.reply_text(f"{len(keywords)} keywords mil gaye. Scraping...")

        numbers = []

        # scraping loop
        for keyword in keywords:
            url = f"https://api.scrapingdog.com/google_maps?api_key={API_KEY}&query={keyword}"

            try:
                res = requests.get(url)
                data = res.json()
            except:
                continue

            # 🔥 FINAL FIXED EXTRACTION
            results = data.get("data")

            if isinstance(results, list):
                for place in results:
                    if "phone" in place and place["phone"]:
                        numbers.append(str(place["phone"]))

        # remove duplicates
        numbers = list(set(numbers))

        if len(numbers) == 0:
            update.message.reply_text("Koi number nahi mila ❌\nBetter keywords use karo")
            return

        # save file
        with open("numbers.txt", "w") as f:
            for num in numbers:
                f.write(num + "\n")

        # send file
        f = open("numbers.txt", "rb")
        update.message.reply_document(document=f)
        f.close()

    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")


# start bot
updater = Updater(BOT_TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(MessageHandler(Filters.document, handle_file))

print("Bot is running...")
updater.start_polling()
updater.idle()
