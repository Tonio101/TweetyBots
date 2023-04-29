import argparse
import logging
import json
import os

from threading import Lock
from models.chatgpt_bot import ChatGPTBot
from models.gcp_pubsub import GcpPubSubClient
from models.logger import Logger
log = \
    Logger.getInstance(
        name='chatgpt_bot',
        fname='/tmp/chatgpt_bot.log'
    ).getLogger()


def parse_config_file(fname: str) -> dict:
    """
    Parse Config File.

    Args:
        fname (string): fpl_updates config file.

    Returns:
        dict: A dict with all the config data.
    """
    with open(os.path.abspath(fname), 'r') as fp:
        data = json.load(fp)
        return data


def main():
    usage = ("{FILE} --config <config_file> --debug").format(FILE=__file__)
    description = 'ChatGPT Bot Updates'
    parser = argparse.ArgumentParser(usage=usage, description=description)
    parser.add_argument("-c", "--config", help="Configuration file",
                        required=True)
    parser.add_argument("--debug", help="Enable verbose logging",
                        action='store_true', required=False)
    parser.set_defaults(debug=False)

    args = parser.parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)

    config = parse_config_file(args.config)
    gcp_pubsub_config = config['gcpPubSub']
    chat_gpt_config = config['chatGptApi']

    pubsub_client = \
        GcpPubSubClient(
            gcp_app_cred_file=gcp_pubsub_config['gcpCredsFile'],
            project_id=gcp_pubsub_config['projectId'],
            topic_id=gcp_pubsub_config['publishId']
        )
    log.debug("Initialized PubSub client")

    lock = Lock()

    os.environ["OPENAI_API_KEY"] = chat_gpt_config['openApiKey']

    chat_gpt_bot = \
        ChatGPTBot(
            msg_type='chatgpt_bot',
            lock=lock,
            pubsub_client=pubsub_client,
            gpt_prompts_file=chat_gpt_config['chatGptPromptsFile']
        )
    log.debug("Initialized ChatGPT Bot")

    chat_gpt_bot.start()
    chat_gpt_bot.join()


if __name__ == "__main__":
    main()
