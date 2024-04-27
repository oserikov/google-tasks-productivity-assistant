from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import os

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def read_bot_token():
    with open("telegram_token.txt", "r") as file:
        return file.read().strip()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) == os.getenv("MY_USER_ID_TG"):
        await update.message.reply_text('Hi! I am your task management bot. Tell me what you have done, and I can update your tasks!')
    else:
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")



def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def run_bot(handle_msg_fn):
    # Read the bot token from the file
    token = read_bot_token()
    
    # Create the Application
    application = Application.builder().token(token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg_fn))
    application.add_error_handler(error)

    # Start the bot
    application.run_polling()
