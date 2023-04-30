import time
import json
import hashlib
import openai
import random
import string
import csv
import re
import os

from time import sleep
from threading import Thread
from models.logger import Logger
log = Logger.getInstance().getLogger()

DEFAULT_GPT_MSG_DELAY = 60 * 60 # Every 30 minutes
OPENAI_RATELIMIT_DELAY = 30 * 60
# DEFAULT_GPT_MSG_DELAY = 2 # Every 30 minutes
DEFAULT_CHAT_GPT_FILE = 'chatgpt_bot_prompts.csv'


class MessageInfo(object):

    def __init__(self, msg_type, timestamp, md5hash, content):
        self.msg_type = msg_type
        self.timestamp = timestamp
        self.md5hash = md5hash
        self.content = content

    def get_msg_info(self) -> dict:
        return ({
                    'msg_type': self.msg_type,
                    'hash': self.md5hash,
                    'content': self.content
                })

    def __str__(self):
        return ("{} {} {}").format(
                    self.msg_type,
                    self.timestamp,
                    self.content
                )


class ChatGPTBot(Thread):

    def __init__(self,
                 msg_type,
                 lock,
                 pubsub_client,
                 config,
                 gpt_message_db=DEFAULT_CHAT_GPT_FILE,
                 chatgpt_message_delay=DEFAULT_GPT_MSG_DELAY):
        super().__init__(daemon=True)
        self.msg_type = msg_type
        self.lock = lock
        self.pubsub_client = pubsub_client
        self.gpt_message_db = gpt_message_db
        self.chatgpt_message_delay = chatgpt_message_delay
        os.environ["OPENAI_API_KEY"] = config['openApiKey']
        # self.chatgpt_prompts = self.get_chatgpt_prompts()
        self.gpt_prompts_file = config['chatGptPromptsFile']

    def acquire(self):
        if self.lock:
            self.lock.acquire()

    def release(self):
        if self.lock:
            self.lock.release()

    def emit_message(self, data):
        if self.pubsub_client:
            self.pubsub_client.publish_message(data)
        else:
            log.info(data)

    def get_chatgpt_prompt(self) -> str:
        chatgpt_prompts = self.get_chatgpt_prompts()
        random_number = \
            random.randint(0, len(chatgpt_prompts) - 1)
        return chatgpt_prompts[random_number]

    def get_chatgpt_prompts(self) -> list:
        with open(self.gpt_prompts_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data['prompts']
        return None

    def get_message_hash(self, message):
        no_punct = ""
        for char in message:
            if char not in string.punctuation and char != " ":
                no_punct += char.lower()
        clean_text = re.sub(r'[^a-zA-Z0-9 ]+', '', no_punct)\
            .replace("\n", "").replace("\r", "")
        return (hashlib.sha256(no_punct.encode()).hexdigest(), clean_text)

    def update_chatgpt_file(self, message):
        message_hashed, no_punct = self.get_message_hash(message)
        self.acquire()
        with open(self.gpt_message_db, 'a', encoding='utf-8') as file:
            file.write(message_hashed + ",\"" +
                       no_punct + "\"\n")
            # file.write(message_hashed + ",\"" +
            #             no_punct + "\",\"" +
            #             message + "\"\n")
        self.release()

    def get_sent_gpt_messages(self) -> set:
        self.acquire()
        message_hash_set = set()
        message_sent_set = set()

        with open(self.gpt_message_db, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            # next(csv_reader) # This skips the header row

            for row in csv_reader:
                message_hash_set.add(row[0].strip())
                message_sent_set.add(row[1].strip())

        # with open(self.gpt_message_db) as f:
        #     lines = f.readlines()
        #     for line in lines:
        #         line = line.split(',')[0].strip()
        #         message_set.add(line)

        self.release()
        return (message_hash_set, message_sent_set)

    def process_message(self, message, md5hash):
        message_info = \
            MessageInfo(self.msg_type, int(time.time()), md5hash, message)
        log.debug(message_info)
        data = json.dumps(message_info.get_msg_info()).encode('utf-8')
        log.debug(data)
        self.emit_message(data)
        self.update_chatgpt_file(message)

    def generate_message(self):
        message_hash_set, messages_sent_set = self.get_sent_gpt_messages()
        # Attempt to get a unique string
        max_retries = 15

        while max_retries > 0:
            prompt = self.get_chatgpt_prompt()
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "assistant", "content": prompt}],
                temperature=0.8,
                max_tokens=2048)

            gpt_response = response.choices[0].message.content
            gpt_response_hash, no_punct_message = self.get_message_hash(gpt_response)

            if (gpt_response_hash not in message_hash_set and
               no_punct_message not in messages_sent_set):
                return (gpt_response, gpt_response_hash)
            max_retries -= 1
            sleep(5)

        return (None, None)

    def run(self):
        while True:
            try:
                (message, md5hash) = self.generate_message()
                if message:
                    self.process_message(message, md5hash)
            except openai.error.RateLimitError as ex:
                log.error(ex)
                sleep(OPENAI_RATELIMIT_DELAY)
            sleep(self.chatgpt_message_delay)
