
import logging
from telegram import Update
from telegram.ext import ContextTypes

import json, os

from task_management import initialize, display_tasks, add_new_tasks, mark_tasks_as_completed
from openai_tools import get_openai_client, system_msg, user_msg, get_system_answer
from bot_tools import run_bot

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


MY_USER_ID = "292749902"
os.environ.setdefault("MY_USER_ID_TG", MY_USER_ID)

service = initialize()
client = get_openai_client()


def analyze_message(message):
    tasks = display_tasks(service)
    history = [system_msg(tasks), user_msg(message)]
    response = get_system_answer(history, client)
    logger.info("Response from GPT-4:", response)
    response_json = json.loads(response.content)
    completed_tasks = response_json.get("completed_tasks", [])
    updated_tasks = response_json.get("updated_tasks", [])
    new_tasks = response_json.get("new_tasks", [])
    return completed_tasks, updated_tasks, new_tasks


# Message handler function
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != MY_USER_ID:
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return

    tg_message = update.message.text
    # Analyze the message using GPT-4
    completed_tasks, updated_tasks, new_tasks = analyze_message(tg_message)
    mark_tasks_as_completed(completed_tasks, service)
    add_new_tasks(new_tasks, service)

    # Respond back to the user with the changes
    response_message = create_response_message(completed_tasks, updated_tasks, new_tasks)
    await update.message.reply_text(response_message)

def create_response_message(completed_tasks, updated_tasks, new_tasks):
    response_lines = []
    if completed_tasks:
        response_lines.append("Completed tasks: " + ", ".join(completed_tasks))
    if updated_tasks:
        response_lines.append("Updated tasks: " + ", ".join(updated_tasks))
    if new_tasks:
        response_lines.append("New tasks added: " + ", ".join(new_tasks))
    
    return "\n".join(response_lines) if response_lines else "No task updates."

if __name__ == '__main__':
    run_bot(handle_message)