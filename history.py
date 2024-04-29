from datetime import datetime
import json

class ConversationHistory:
    """
    A class to manage the conversation history.

    Attributes
    ----------
    filename : str or False
        The name of the file where the conversation history is stored. If set to False, the conversation history is not stored.
    history : dict
        The conversation history. The keys are user IDs and the values are lists of messages.
        Each message is a dictionary with the following keys:
        - 'sender': The sender of the message ('user' or 'bot').
        - 'message': The content of the message.
        - 'time': The time the message was sent, in ISO 8601 format.
    """
    def __init__(self, filename='conversation_history.json'):
        """
        Initialize a ConversationHistory object.

        Parameters
        ----------
        filename : str or False, optional
            The name of the file where the conversation history is stored. If set to False, the conversation history is not stored. By default, 'conversation_history.json'.
        """
        self.filename = filename
        self.history = self.load_history()

    def load_history(self):
        try:
            if self.filename == False:
                return {}
            with open(self.filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            print("No existing conversation history found.")
            print(e)
            return {}

    def save_history(self):
        with open(self.filename, 'w') as f:
            json.dump(self.history, f)

    def add_message(self, user_id, sender, message):
        if not isinstance(message, dict):
            raise ValueError("Message must be a dictionary with fields 'role' and 'content'.")
        if user_id not in self.history:
            self.history[user_id] = []
        self.history[user_id].append({
            "sender": sender,
            "message": message,
            "time": datetime.now().isoformat()
        })
        if self.filename:
            self.save_history()

    def get_history(self, user_id):
        """
        Get the conversation history for a given user ID.

        Parameters
        ----------
        user_id : str
            The ID of the user.

        Returns
        -------
        list
            The conversation history for the user. Each message is a dictionary with the following keys:
            - 'sender': The sender of the message ('user' or 'bot').
            - 'message': The content of the message.
            - 'time': The time the message was sent, in ISO 8601 format.
        """
        return self.history.get(user_id, [])
