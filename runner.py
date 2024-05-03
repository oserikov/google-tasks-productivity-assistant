
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
conv_history = ConversationHistory()

def analyze_message(message):
    tasks = display_tasks(service)
    task_manager_agent.update_tasks(tasks)
    response = task_manager_agent.get_system_answer(user_msg=message)
    logger.info("Response from GPT-4:", response)
    response_json = json.loads(response.content)
    
    completed_tasks = response_json.get("completed_tasks", [])
    new_tasks_from_completed = [t for t in completed_tasks if t not in tasks]
    completed_tasks = [t for t in completed_tasks if t in tasks]
    
    updated_tasks = response_json.get("updated_tasks", [])
    new_tasks_from_updated = [t for t in updated_tasks if t not in tasks]
    updated_tasks = [t for t in updated_tasks if t in tasks]

    new_tasks = response_json.get("new_tasks", [])
    new_tasks = new_tasks + new_tasks_from_completed + new_tasks_from_updated
    return completed_tasks, updated_tasks, new_tasks

def chat_with_gpt(history, user_id):
    tasks = display_tasks(service)
    task_analyzer_agent.update_tasks(tasks)
    response = task_analyzer_agent.get_system_answer_for_history(history=history, user_id=user_id)
    return response.content

def is_task_progress(message):
    return message.lower().startswith('!!progress')

def update_task_tracker(service, message):
    completed_tasks, updated_tasks, new_tasks = analyze_message(message)
    mark_tasks_as_completed(completed_tasks, service)
    add_new_tasks(new_tasks, service)

    return completed_tasks, updated_tasks, new_tasks

ENSURE_NO_TASKS_ARE_MISSED_PROMPT = """
I was speaking to a bot about my tasks. 
I wrote a message and bot replied. 
Analyze my message and tell which task I have accomplished.
Use bot's answer as a hint to update my task list.
===
Here goes my message:
{message}
===
Here goes bot's response:
{response}
"""

# Message handler function
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)
    if user_id != MY_USER_ID:
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return

    tg_message = update.message.text
    conv_history.add_message(user_id, "user", {'role': 'user', 'content': tg_message})

    if not is_task_progress(tg_message):
        response_message = chat_with_gpt(conv_history, user_id)
        additional_tasks_analysis_msg = ENSURE_NO_TASKS_ARE_MISSED_PROMPT.format(message=tg_message, response=response_message) 
        completed_tasks, updated_tasks, new_tasks = update_task_tracker(service, additional_tasks_analysis_msg)
        response_message = response_message + "\n\n\nAnalysis results:\n" + create_response_message(completed_tasks, updated_tasks, new_tasks)
    else:
        completed_tasks, updated_tasks, new_tasks = update_task_tracker(service, tg_message)
        # Respond back to the user with the changes
        response_message = create_response_message(completed_tasks, updated_tasks, new_tasks)

    conv_history.add_message(user_id, "bot", {'role':'assistant','content':response_message})

    MAX_MESSAGE_LENGTH = 4096
    messages = []
    current_message = ""
    for line in response_message.split('\n'):
        if len(current_message) + len(line) + 1 > MAX_MESSAGE_LENGTH:  # +1 for the newline character
            messages.append(current_message)
            current_message = line
        else:
            current_message += '\n' + line if current_message else line
    messages.append(current_message)  # append the last message

    for message in messages:
        await update.message.reply_text(message)


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