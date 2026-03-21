import os
import asyncio
import aiohttp
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

CONCURRENCY = 5
CHUNK_SIZE = 100
OUTPUT_FILE = "output.txt"


def split_text_keywords(text: str):
    text = text.strip()
    if not text:
        return []

    if "\n" in text:
        parts = text.splitlines()
    else:
        parts = text.split(",")

    return [p.strip() for p in parts if p.strip()]


async def fetch_keyword(session, sem, keyword):
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
                chunk_results = []

                for place in results:
                    phone = place.get("phone")
                    name = place.get("title")

                    if phone and name:
                        chunk_results.append(f"{phone} : {name}")

                return chunk_results

        except Exception:
            return []


async def process_chunk(chunk):
    sem = asyncio.Semaphore(CONCURRENCY)
    connector = aiohttp.TCPConnector(limit=CONCURRENCY)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_keyword(session, sem, keyword) for keyword in chunk]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    final_results = []
    for item in results:
        if isinstance(item, list):
            final_results.extend(item)

    return final_results


def read_keywords_from_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def save_results(results):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in results:
            f.write(item + "\n")


def handle_input(update: Update, context: CallbackContext):
    try:
        message = update.message
        keywords = []

        # Bot alive reply
        message.reply_text("🚀 Bot started...\nProcessing your request...")

        # Case 1: .txt file input
        if message.document:
            document = message.document

            if not document.file_name.lower().endswith(".txt"):
                message.reply_text("Only .txt file allowed")
                return

            tg_file = document.get_file()
            input_file = "keywords.txt"
            tg_file.download(input_file)

            keywords = read_keywords_from_txt(input_file)

        # Case 2: plain text input
        elif message.text:
            keywords = split_text_keywords(message.text)

        else:
            message.reply_text("Send .txt file ya plain text")
            return

        if not keywords:
            message.reply_text("Koi keyword nahi mila")
            return

        total_keywords = len(keywords)
        all_results = []
        processed = 0

        for i in range(0, total_keywords, CHUNK_SIZE):
            chunk = keywords[i:i + CHUNK_SIZE]

            chunk_results = asyncio.run(process_chunk(chunk))
            all_results.extend(chunk_results)

            processed += len(chunk)
            message.reply_text(f"✅ Processed {processed}/{total_keywords} keywords")

        # remove duplicates while preserving order
        unique_results = list(dict.fromkeys(all_results))

        if not unique_results:
            message.reply_text("Koi data nahi mila ❌")
            return

        save_results(unique_results)

        with open(OUTPUT_FILE, "rb") as f:
            message.reply_document(document=f)

        message.reply_text("🎉 Done!")

    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")


def main():
    if not API_KEY:
        raise ValueError("API_KEY environment variable not set")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable not set")

    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # .txt file input
    dp.add_handler(MessageHandler(Filters.document, handle_input))

    # plain text input
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_input))

    print("Bot running...")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
