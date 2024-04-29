from openai import OpenAI
import logging
from history import ConversationHistory
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIAgent:

    DEFAULT_SYSTEM_PROMPT = "You are an intelligent assistant. You can help users with a variety of tasks. Please provide clear and concise responses to user requests."

    def __init__(self, model, system_prompt=None):
        self.model = model
        if system_prompt is None:
            system_prompt = self.DEFAULT_SYSTEM_PROMPT
        self.system_prompt = system_prompt
        self.client = self.get_openai_client()
        self.history = ConversationHistory(filename="openai_conversation_history.json")

    # Function to read the OPENAI token from a file
    def read_openai_token(self):
        with open("chatgpt_key.txt", "r") as file:
            return file.read().strip()

    def get_openai_client(self):
        return OpenAI(api_key=self.read_openai_token())

    def system_msg(self):
        return {"role": "system", "content": self.system_prompt}

    def user_msg(self, text):
        return {"role": "user", "content": text}

    def get_system_answer(self, history=None, user_msg=None):
        if history is not None:
            return self.client.chat.completions.create(messages=history, model=self.model).choices[0].message
        else:
            if self.history.get_history('openai') == []:
                print("No history found")
                self.history.add_message('openai', 'system', self.system_msg())
                print("System message added")
            print("Before adding user message")
            self.history.add_message('openai', 'user', self.user_msg(user_msg))
            print("After adding user message")
            history_to_use = self.history.get_history('openai')
            print("History to use:", history_to_use)
            system_answer = self.client.chat.completions.create(
                messages=history_to_use, 
                model=self.model).choices[0].message
            print("System answer:", system_answer)
            self.history.add_message('openai', 'system', system_answer)
            print("System message added")
            return system_answer


class TaskManagerAgent(OpenAIAgent):
    TASK_UPDATE_PROMPT = "You are an intelligent task manager assistant. When user tells you what he's been working on, you will analyze his message to identify: \n1. Tasks he completed.\n2. Tasks he made progress on that are already in our list.\n3. New tasks that user might want to add.\nUser need clear and concise updates to manage tasks effectively.\nYou will output json with fields 'completed_tasks', 'updated_tasks' and 'new_tasks', respectively. \n\n"

    def __init__(self, model):
        super().__init__(model, self.TASK_UPDATE_PROMPT)

    def system_msg(self, tasks):
        SYSTEM_PROMPT = (self.system_prompt +
                        "User tasks are:"
                        f"{'|'.join(tasks)}"
                        )
        return {"role": "system", "content": SYSTEM_PROMPT}
    
    def get_system_answer(self, history=None, user_msg=None, tasks=None):
        if tasks is None:
            tasks = []
        if history is not None:
            return self.client.chat.completions.create(messages=history, model=self.model).choices[0].message
        else:
            print("No history will be stored")
            self.history = ConversationHistory(filename=False)
            print("History created")
            self.history.add_message('openai', 'system', self.system_msg(tasks))
            print("System message added")
            self.history.add_message('openai', 'user', self.user_msg(user_msg))
            print("User message added")
            messages_to_send = [el['message'] for el in  self.history.get_history('openai')]
            print("Messages to send:", messages_to_send)
            system_answer = self.client.chat.completions.create(
                messages=messages_to_send, 
                model=self.model).choices[0].message
            print("System answer:", system_answer)
            return system_answer
        
    
class TaskAnalyzerAgent(OpenAIAgent):
    TASK_ANALYSIS_PROMPT = "You are an intelligent task analyzer assistant. When the user tells you about their tasks, you will analyze their message to identify: \n1. The progress made on each task.\n2. Any challenges faced.\n3. Suggestions for improving productivity. You will attempt to answer user questions in a very useful manner, helping him to organize his tasks and identify how to accomplish them. \nYou will output a markdown formatted answer. \n\n"

    def __init__(self, model):
        super().__init__(model, self.TASK_ANALYSIS_PROMPT)

    def system_msg(self, tasks):
        SYSTEM_PROMPT = (self.system_prompt +
                        "User tasks are:"
                        f"{'|'.join(tasks)}"
                        )
        return {"role": "system", "content": SYSTEM_PROMPT}

    def get_system_answer(self, user_msg=None, tasks=None, user_history=None):
        if tasks is None:
            tasks = []
       
        if user_history is not None:
            self.history = ConversationHistory(filename=False)
            self.history.add_message('openai', 'system', self.system_msg(tasks))
            for msg in user_history:
                print(msg)
                self.history.add_message('openai', msg['sender'], self.user_msg(msg['message']))
        else:
            self.history.add_message('openai', 'user', self.user_msg(user_msg))
        messages_to_send = [el['message'] for el in  self.history.get_history('openai')]
        print("Messages to send:", messages_to_send)
        system_answer = self.client.chat.completions.create(
            messages=messages_to_send, 
            model=self.model).choices[0].message
        return system_answer