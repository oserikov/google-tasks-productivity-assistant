import logging
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from datetime import datetime

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
import json

def initialize():
    """
    Initialize the Google Tasks API service
    :return: The service object"""
    scopes = ['https://www.googleapis.com/auth/tasks']

    # Path to the credentials and token files
    creds = None
    token_path = 'token.json'
    creds_path = 'client_secret.json'

    # Load credentials from the token file if it exists
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, scopes)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    # Build the service object
    service = build('tasks', 'v1', credentials=creds)
    return service

def add_task(service, task_title):
    """
    Add a task to the default task list
    :param service: The service object
    :param task_title: The title of the task to add
    :return: None"""
    task = {'title': task_title}
    result = service.tasks().insert(tasklist='@default', body=task).execute()
    logger.info(f"Task added: {result['title']}")

def dump_tasks(tasks):
    now = datetime.now()
    # Format date and time
    filename = now.strftime("dump/keep_tasks_%H:%M:%S_%d:%m:%Y.json")
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    # Dump tasks to JSON file
    with open(filename, 'w') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

def display_tasks(service):
    """
    Display all incomplete tasks
    :param service: The service object
    :return: None"""
    results = service.tasks().list(tasklist='@default', showHidden=False, showCompleted=False).execute()
    dump_tasks(results)
    items = results.get('items', [])

    if not items:
        logger.info('No incomplete tasks found.')
    else:
        logger.info('Your incomplete tasks:')
        for item in items:
            logger.info(item['title'])
    
    return [item['title'] for item in items]

def mark_task_as_done(service, task_title):
    """
    Mark a task as completed based on its title
    :param service: The service object
    :param task_title: The title of the task to mark as completed
    :return: None"""
    # Retrieve the list of tasks
    results = service.tasks().list(tasklist='@default', showHidden=False).execute()
    items = results.get('items', [])

    # Find the task by title and mark it as completed
    task_found = False
    for item in items:
        if item['title'] == task_title:
            task_found = True
            item['status'] = 'completed'
            service.tasks().update(tasklist='@default', task=item['id'], body=item).execute()
            logger.info(f"Task marked as completed: {item['title']}")
            break

    if not task_found:
        logger.info("Task not found.")


def mark_tasks_as_completed(completed_tasks, service):
    for task in completed_tasks:
        mark_task_as_done(service, task)

def add_new_tasks(new_tasks, service):
    for task in new_tasks:
        add_task(service, task)