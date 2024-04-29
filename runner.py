
import logging
from telegram import Update
from telegram.ext import ContextTypes

import json, os

from task_management import initialize, display_tasks, add_new_tasks, mark_tasks_as_completed
from openai_tools import OpenAIAgent, TaskManagerAgent, TaskAnalyzerAgent
from bot_tools import run_bot

from history import ConversationHistory

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


MY_USER_ID = "292749902"
os.environ.setdefault("MY_USER_ID_TG", MY_USER_ID)

service = initialize()
task_manager_agent = TaskManagerAgent("gpt-4")
task_analyzer_agent = TaskAnalyzerAgent("gpt-4")


def analyze_message(message):
    tasks = display_tasks(service)
    print("Tasks obtained:", tasks)
    response = task_manager_agent.get_system_answer(user_msg=message, tasks=tasks)
    print("Response obtained:", response)
    logger.info("Response from GPT-4:", response)
    response_json = json.loads(response.content)
    print("Response JSON obtained:", response_json)
    completed_tasks = response_json.get("completed_tasks", [])
    print("Completed tasks obtained:", completed_tasks)
    updated_tasks = response_json.get("updated_tasks", [])
    print("Updated tasks obtained:", updated_tasks)
    new_tasks = response_json.get("new_tasks", [])
    print("New tasks obtained:", new_tasks)
    return completed_tasks, updated_tasks, new_tasks

def chat_with_gpt(history):
    tasks = display_tasks(service)
    response = task_analyzer_agent.get_system_answer(user_history=history, tasks=tasks)
    return response.content

# Global variable to store conversation history
conv_history = ConversationHistory()

# Load conversation history from file
try:
    with open('conversation_history.json', 'r') as f:
        conversation_history = json.load(f)
except FileNotFoundError:
    print("No existing conversation history found.")

def is_task_progress(message):
    return message.lower().startswith('!!progress')

# Message handler function
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Starting handle_message function")

    user_id = str(update.effective_user.id)
    if user_id != MY_USER_ID:
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return
    print("User ID obtained:", user_id)

    tg_message = update.message.text
    conv_history.add_message(user_id, "user", tg_message)
    print("Message obtained and put to history:", tg_message)

    print("Starting message analysis")
    # Analyze the message using GPT-4
    if is_task_progress(tg_message):
        print("Analyzing message")
        completed_tasks, updated_tasks, new_tasks = analyze_message(tg_message)
        print("Message analyzed")
        mark_tasks_as_completed(completed_tasks, service)
        add_new_tasks(new_tasks, service)
        print("Keep api updated with new tasks and completed tasks")

        # Respond back to the user with the changes
        response_message = create_response_message(completed_tasks, updated_tasks, new_tasks)
        print("Response message created")
    else:
        print("Chatting with GPT-4")
        response_message = chat_with_gpt(conv_history.history[user_id])
        print("GPT-4 response obtained")
    print("Sending response message")
    conv_history.add_message(user_id, "bot", response_message)
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