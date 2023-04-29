import csv
import unittest

from models.chatgpt_bot import ChatGPTBot

DEFAULT_CHAT_GPT_FILE = 'chatgpt_bot_prompts.csv'


class TestLogger(unittest.TestCase):

    def test_create(self):
        chat_gpt_bot = \
            ChatGPTBot(
                msg_type='chatgpt_bot',
                lock=None,
                pubsub_client=None
            )

        chat_gpt_bot.start()

        test_prompts = []
        with open(DEFAULT_CHAT_GPT_FILE, 'r') as file:
            csv_reader = csv.reader(file)
            # next(csv_reader) # This skips the header row

            for row in csv_reader:
                test_prompts.append(row[2])

        for prompt in test_prompts:
            output = chat_gpt_bot.get_message_hash(prompt)
            print(output)

        # chat_gpt_bot.stop()
        chat_gpt_bot.join()
        # self.assertTrue()


if __name__ == '__main__':
    unittest.main()

