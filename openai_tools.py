from openai import OpenAI
import logging
from history import ConversationHistory
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


#todo agents now are bad at handling own history, I don't use it in fact.

class OpenAIAgent:

    DEFAULT_SYSTEM_PROMPT = "You are an intelligent assistant. You can help users with a variety of tasks. Please provide clear and concise responses to user requests."

    def __init__(self, model, system_prompt=None):
        self.model = model
        if system_prompt is None:
            system_prompt = self.DEFAULT_SYSTEM_PROMPT
        self.system_prompt = system_prompt
        self.client = self.get_openai_client()
        self.history = ConversationHistory(filename="openai_conversation_history.json")
        self.system_prompt_functions = dict()

    # Function to read the OPENAI token from a file
    def read_openai_token(self):
        with open("chatgpt_key.txt", "r") as file:
            return file.read().strip()

    def get_openai_client(self):
        return OpenAI(api_key=self.read_openai_token())

    def system_msg(self):
        # given system_prompt as template_string, and field values stored in self.system_prompt_functions, return formatted string
        # but as system_prompt_functions are functions, they have to be executed first
        prompt_values_dict = dict()
        for wildcard, function in self.system_prompt_functions.items():
            prompt_values_dict[wildcard] = function()
        system_prompt = self.system_prompt.format(**prompt_values_dict)
        return {"role": "system", "content": system_prompt}

    def user_msg(self, text:str):
        return {"role": "user", "content": text}

    def call_openai(self, history:ConversationHistory):
        messages_to_send = [el['message'] for el in  history.get_history('openai')]
        print(messages_to_send)
        system_answer = self.client.chat.completions.create(
            messages=messages_to_send, 
            model=self.model).choices[0].message
        return system_answer

    def get_system_answer_for_history(self, history:ConversationHistory, user_id='openai'):
            # todo check if conversationhistory contains system prompt
            first_message = history.get_history(user_id)
            new_history = ConversationHistory(filename=False)
            if not first_message or first_message[0]['sender'] != 'system':
                new_history.add_message('openai', 'system', self.system_msg())
            for msg in history.get_history(user_id):
                new_history.add_message('openai', msg['sender'], msg['message'])
                
            history = new_history
            return self.call_openai(history)

    def get_system_answer(self, user_msg:str=None):
        if self.history.get_history('openai') == []:
            self.history.add_message('openai', 'system', self.system_msg())
        self.history.add_message('openai', 'user', self.user_msg(user_msg))
        system_answer = self.call_openai(self.history)
        self.history.add_message('openai', 'system', system_answer)
        return system_answer


class TaskManagerAgent(OpenAIAgent):
    TASK_UPDATE_PROMPT = "You are an intelligent task manager assistant. When user tells you what he's been working on, you will analyze his message to identify: \n1. Tasks he completed.\n2. Tasks he made progress on that are already in our list.\n3. New tasks that user might want to add.\nUser need clear and concise updates to manage tasks effectively.\nYou will output json with fields 'completed_tasks', 'updated_tasks' and 'new_tasks', respectively. You may observe 'Analysis results' section in the conversation history. You DON'T HAVE to write this text: it is automatically generated later. Current user tasks are: \n\n {tasks}"

    def __init__(self, model):
        # todo cant I write better?
        super().__init__(model, self.TASK_UPDATE_PROMPT)
        self.system_prompt_functions = {'tasks': self._get_tasks}
        self._tasks = None # should be updated on each use

    def _get_tasks(self):
        return '|'.join(self._tasks)

    def update_tasks(self, tasks):
        self._tasks = tasks

    def get_system_answer(self, user_msg=None):
        # todo it would be better to have history class that does not actually store history instead of implementing it here
        history = ConversationHistory(filename=False)
        history.add_message('openai', 'system', self.system_msg())
        history.add_message('openai', 'user', self.user_msg(user_msg))
        system_answer = self.call_openai(history)
        return system_answer
        
    
class TaskAnalyzerAgent(OpenAIAgent):
    TASK_ANALYSIS_PROMPT = "You are an intelligent task analyzer assistant. When the user tells you about their tasks, you will analyze their message to identify: \n1. The progress made on each task.\n2. Any challenges faced.\n3. Suggestions for improving productivity. You will attempt to answer user questions in a very useful manner, helping him to organize his tasks and identify how to accomplish them. \nYou will output a markdown formatted answer. \n\nCurrent user tasks are: {tasks}"

    def __init__(self, model):
        super().__init__(model, self.TASK_ANALYSIS_PROMPT)
        self.system_prompt_functions = {'tasks': self._get_tasks}
        self._tasks = None # should be updated on each use

    def _get_tasks(self):
        return '|'.join(self._tasks)
    
    def update_tasks(self, tasks):
        self._tasks = tasks

    def get_system_answer(self, user_msg=None):
        raise NotImplementedError("Use get_system_answer_for_history.")