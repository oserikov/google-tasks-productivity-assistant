from openai import OpenAI
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)



# Function to read the OPENAI token from a file
def read_openai_token():
    with open("chatgpt_key.txt", "r") as file:
        return file.read().strip()
    
def get_openai_client():
    return OpenAI(api_key=read_openai_token())

def system_msg(tasks):
    SYSTEM_PROMPT = ("You are an intelligent task manager assistant. When user tells you what he's been "
                    "working on, you will analyze his message to identify: \n"
                    "1. Tasks he completed.\n"
                    "2. Tasks he made progress on that are already in our list.\n"
                    "3. New tasks that user might want to add.\n"
                    "User need clear and concise updates to manage tasks effectively.\n"
                    "You will output json with fields 'completed_tasks', 'updated_tasks' and 'new_tasks', respectively. \n\n"
                    "User tasks are:"
                    f"{'|'.join(tasks)}"
                    )
    return {"role": "system", "content": SYSTEM_PROMPT}

def user_msg(text):
    return {"role": "user", "content": text}

def get_system_answer(history, client):
    return client.chat.completions.create(messages=history, model="gpt-4").choices[0].message
