import requests
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send /scrape to start scraping")

async def scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Scraping started...")

    keywords = open("keywords.txt").read().splitlines()
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

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("scrape", scrape))

app.run_polling()
