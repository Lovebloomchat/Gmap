import os
import asyncio
import aiohttp
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler

API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

CONCURRENCY = 1
CHUNK_SIZE = 100        # 🔥 processing
OUTPUT_BATCH = 200      # 🔥 output trigger
OUTPUT_FILE = "final_output.txt"


def start(update, context):
    update.message.reply_text("🤖 Bot chal raha hai!\nTxt ya text bhejo")


def split_text_keywords(text):
    text = text.strip()
    if "\n" in text:
        return [x.strip() for x in text.splitlines() if x.strip()]
    else:
        return [x.strip() for x in text.split(",") if x.strip()]


async def fetch(session, sem, keyword):
    url = "https://api.scrapingdog.com/google_maps"
    params = {"api_key": API_KEY, "query": keyword}

    async with sem:
        try:
            async with session.get(url, params=params, timeout=30) as res:
                data = await res.json(content_type=None)

                results = data.get("search_results") or data.get("data") or []
                temp = []

                for place in results:
                    name = place.get("title")
                    phone = place.get("phone") or "N/A"

                    if name:
                        temp.append(f"{phone} : {name}")

                await asyncio.sleep(1)
                return temp

        except:
            return []


async def process_chunk(chunk):
    sem = asyncio.Semaphore(CONCURRENCY)

    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, sem, kw) for kw in chunk]
        results = await asyncio.gather(*tasks)

    final = []
    for r in results:
        final.extend(r)

    return final


def handle_input(update: Update, context: CallbackContext):
    try:
        message = update.message
        message.reply_text("🚀 Processing started...")

        keywords = []

        if message.document:
            doc = message.document
            file = doc.get_file()
            file.download("keywords.txt")

            with open("keywords.txt", "r", encoding="utf-8") as f:
                content = f.read().replace("\r", "")
                keywords = [line.strip() for line in content.split("\n") if line.strip()]

        elif message.text:
            keywords = split_text_keywords(message.text)

        if not keywords:
            message.reply_text("No keywords found ❌")
            return

        total = len(keywords)
        all_results = []
        temp_buffer = []
        processed = 0
        part_number = 1

        for i in range(0, total, CHUNK_SIZE):
            chunk = keywords[i:i + CHUNK_SIZE]

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            chunk_results = loop.run_until_complete(process_chunk(chunk))
            loop.close()

            processed += len(chunk)
            all_results.extend(chunk_results)
            temp_buffer.extend(chunk_results)

            # 🔥 jab 200 result ho jaye
            if len(temp_buffer) >= OUTPUT_BATCH:
                filename = f"output_part_{part_number}.txt"

                with open(filename, "w", encoding="utf-8") as f:
                    for item in temp_buffer:
                        f.write(item + "\n")

                with open(filename, "rb") as f:
                    message.reply_document(f)

                temp_buffer = []
                part_number += 1

            message.reply_text(f"✅ Processed {processed}/{total}")

        # 🔥 remaining buffer
        if temp_buffer:
            filename = f"output_part_{part_number}.txt"

            with open(filename, "w", encoding="utf-8") as f:
                for item in temp_buffer:
                    f.write(item + "\n")

            with open(filename, "rb") as f:
                message.reply_document(f)

        # 🔹 final file
        unique = list(dict.fromkeys(all_results))

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for item in unique:
                f.write(item + "\n")

        with open(OUTPUT_FILE, "rb") as f:
            message.reply_document(f)

        message.reply_text("🎉 Done!")

    except Exception as e:
        message.reply_text(f"Error: {str(e)}")


def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document | Filters.text, handle_input))

    print("Bot running...")

    updater.bot.delete_webhook()
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
