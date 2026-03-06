import asyncio
import logging
import os
from functools import wraps

from dotenv import load_dotenv
load_dotenv()

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from agent import run_agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ALLOWED_USER_ID = int(os.environ["TELEGRAM_USER_ID"])


def restricted(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != ALLOWED_USER_ID:
            await update.message.reply_text("Unauthorized.")
            return
        return await func(update, context)
    return wrapper


@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Noptiera bot ready.\n\n"
        "Send a URL to ingest it.\n"
        "Send any other text to search."
    )


@restricted
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    await update.message.reply_text("Thinking...")
    try:
        reply = await asyncio.get_event_loop().run_in_executor(None, run_agent, text)
    except Exception as e:
        log.exception("Agent failed")
        await update.message.reply_text(f"Error: {e}")
        return
    await update.message.reply_text(reply, disable_web_page_preview=True)


if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    log.info("Bot starting, allowed user ID: %d", ALLOWED_USER_ID)
    app.run_polling()
