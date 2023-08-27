import argparse
import logging
import json
import os

from threading import Lock
from models.twitter_bot import TwitterBot
from models.gcp_pubsub import GcpPubSubClient
from models.logger import Logger
log = Logger.getInstance().getLogger()


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
    description = 'Twitter Bot Updates'
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
    twitterConfig = config['twitterbot']
    gcpPubSubConfig = config['gcpPubSub']

    pubsub_client = \
        GcpPubSubClient(
            gcp_app_cred_file=gcpPubSubConfig['gcpCredsFile'],
            project_id=gcpPubSubConfig['projectId'],
            topic_id=gcpPubSubConfig['publishId']
        )

    lock = Lock()
    # TODO: Only listen to FPL Updates during FPL Gameweek
    # fpl_updates = \
    #    TwitterBot(
    #        lock=lock,
    #        twitter_bearer_token=twitterConfig['apiBearerToken'],
    #        pubsub_client=pubsub_client,
    #        twitter_id="Fpl_Updates",
    #        tweets_id_db=twitterConfig['tweetsIdDb']
    #    )

    # fpl_alerts = \
    #     TwitterBot(
    #         msg_type='fpl_twitter_bot',
    #         lock=lock,
    #         consumer_key=twitterConfig['consumerKey'],
    #         consumer_secret=twitterConfig['consumerSecret'],
    #         access_token=twitterConfig['accessToken'],
    #         access_token_secret=twitterConfig['accessTokenSecret'],
    #         pubsub_client=pubsub_client,
    #         twitter_id="FPL_Alerts",
    #         tweets_id_db=twitterConfig['tweetsIdDb']
    #     )

    inspirational_tweets = \
        TwitterBot(
            msg_type='twitter_bot',
            lock=lock,
            consumer_key=twitterConfig['consumerKey'],
            consumer_secret=twitterConfig['consumerSecret'],
            access_token=twitterConfig['accessToken'],
            access_token_secret=twitterConfig['accessTokenSecret'],
            pubsub_client=pubsub_client,
            twitter_id="SeffSaid",
            tweet_delay=(30 * 60),
            use_as_is=True,
            tweets_id_db=twitterConfig['tweetsIdDb']
        )

    # funny_tweets = \
    #     TwitterBot(
    #         msg_type='twitter_bot',
    #         lock=lock,
    #         consumer_key=twitterConfig['consumerKey'],
    #         consumer_secret=twitterConfig['consumerSecret'],
    #         access_token=twitterConfig['accessToken'],
    #         access_token_secret=twitterConfig['accessTokenSecret'],
    #         pubsub_client=pubsub_client,
    #         twitter_id="Dadsaysjokes",
    #         tweet_delay=(30 * 60),
    #         use_as_is=True,
    #         tweets_id_db=twitterConfig['tweetsIdDb']
    #     )

    # fpl_updates.start()
    # fpl_alerts.start()
    inspirational_tweets.start()
    # funny_tweets.start()
    # fpl_updates.join()
    # fpl_alerts.join()
    inspirational_tweets.join()
    # funny_tweets.join()


if __name__ == "__main__":
    main()
