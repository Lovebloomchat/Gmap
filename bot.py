import os
import asyncio
import aiohttp
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler

API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

CONCURRENCY = 5
CHUNK_SIZE = 100
OUTPUT_FILE = "output.txt"


# 🔹 Start command
def start(update, context):
    update.message.reply_text("🤖 Bot chal raha hai!\nTxt ya text bhejo")


# 🔹 Text split
def split_text_keywords(text):
    text = text.strip()
    if "\n" in text:
        return [x.strip() for x in text.splitlines() if x.strip()]
    else:
        return [x.strip() for x in text.split(",") if x.strip()]


# 🔹 Async scraping
async def fetch(session, sem, keyword):
    url = "https://api.scrapingdog.com/google_maps"
    params = {
        "api_key": API_KEY,
        "query": keyword
    }

    async with sem:
        try:
            async with session.get(url, params=params, timeout=30) as res:
                data = await res.json(content_type=None)

                results = data.get("search_results") or data.get("data") or []
                temp = []

                for place in results:
                    phone = place.get("phone")
                    name = place.get("title")

                    if phone and name:
                        temp.append(f"{phone} : {name}")

                return temp

        except:
            return []


# 🔹 Chunk processing
async def process_chunk(chunk):
    sem = asyncio.Semaphore(CONCURRENCY)

    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, sem, kw) for kw in chunk]
        results = await asyncio.gather(*tasks)

    final = []
    for r in results:
        final.extend(r)

    return final


# 🔹 Main handler
def handle_input(update: Update, context: CallbackContext):
    try:
        message = update.message
        message.reply_text("🚀 Processing started...")

        keywords = []

        # 📁 File input
        if message.document:
            doc = message.document

            if not doc.file_name.endswith(".txt"):
                message.reply_text("Only .txt allowed")
                return

            file = doc.get_file()
            file.download("keywords.txt")

            with open("keywords.txt", "r", encoding="utf-8") as f:
                keywords = [x.strip() for x in f if x.strip()]

        # 📝 Text input
        elif message.text:
            keywords = split_text_keywords(message.text)

        if not keywords:
            message.reply_text("No keywords found ❌")
            return

        total = len(keywords)
        all_results = []
        processed = 0

        # 🔥 Chunk loop
        for i in range(0, total, CHUNK_SIZE):
            chunk = keywords[i:i + CHUNK_SIZE]

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            chunk_results = loop.run_until_complete(process_chunk(chunk))
            loop.close()

            all_results.extend(chunk_results)
            processed += len(chunk)

            message.reply_text(f"✅ Processed {processed}/{total}")

        # 🔹 remove duplicates
        unique = list(dict.fromkeys(all_results))

        if not unique:
            message.reply_text("Koi data nahi mila ❌")
            return

        # 🔹 save file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for item in unique:
                f.write(item + "\n")

        # 🔹 send file
        with open(OUTPUT_FILE, "rb") as f:
            message.reply_document(f)

        message.reply_text("🎉 Done!")

    except Exception as e:
        message.reply_text(f"Error: {str(e)}")


# 🔹 Main function
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document | Filters.text, handle_input))

    print("Bot running...")

    updater.bot.delete_webhook()  # 🔥 important
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
