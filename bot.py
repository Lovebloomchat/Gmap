import requests
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # file download
    file = await update.message.document.get_file()
    await file.download_to_drive("keywords.txt")

    await update.message.reply_text("Scraping started...")

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

    # save numbers
    with open("numbers.txt", "w") as f:
        for num in numbers:
            f.write(num + "\n")

    # send result
    await update.message.reply_document(document=open("numbers.txt", "rb"))


# app setup
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

print("Bot is running...")
app.run_polling()
