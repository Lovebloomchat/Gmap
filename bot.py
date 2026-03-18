import requests
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    await file.download_to_drive("keywords.txt")

    await update.message.reply_text("File received! Scraping started...")

    with open("keywords.txt", "r") as f:
        keywords = f.read().splitlines()

    numbers = []

    for keyword in keywords:
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

    await update.message.reply_document(document=open("numbers.txt", "rb"))

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

app.run_polling()app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("scrape", scrape))

app.run_polling()
