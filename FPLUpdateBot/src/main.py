import argparse
import datetime
import json
import tweepy
import pytz
import sys
import os

from threading import Thread
from time import sleep
from gcp_pubsub import GcpPubSubClient


USER_ID = "Fpl_Updates"
TWEET_QUERY = 'from:Fpl_Updates -is:retweet'
# TWEET_FIELDS = ['context_annotations', 'created_at']
TWEET_FIELDS = ['created_at']
MAX_TWEETS_PER_QUERY = 10

TWEET_IDS = 'tweet_id.db'


class TweetInfo(object):

    def __init__(self, id, timestamp, content):
        self.id = id
        self.timestamp = timestamp
        self.content = content

    def get_tweet_dict(self):
        return ({
                # "timestamp": self.timestamp,
                "content": self.content
                })


class FPLUpdates(Thread):

    def __init__(self, tweet_client, pubsub_client):
        # Call the Thread class's init function
        Thread.__init__(self)
        self.client = tweet_client
        self.pubsub_client = pubsub_client

    def get_recent_fpl_tweets_upate(self):
        result = dict()
        now = datetime.datetime.now()
        # current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        utc_now = pytz.utc.localize(now)
        pst_now = utc_now.astimezone(pytz.timezone("America/Los_Angeles"))
        current_time = pst_now.strftime("%Y-%m-%d %H:%M:%S")

        try:
            tweets = self.client.search_recent_tweets(
                    query=TWEET_QUERY,
                    tweet_fields=TWEET_FIELDS,
                    max_results=MAX_TWEETS_PER_QUERY)

            now = datetime.datetime.now()
            print("Successfully returned {} tweets at {}".format(
                len(tweets.data),
                current_time
            ))

            for tweet in tweets.data:
                tweet_info = \
                        TweetInfo(tweet.id, tweet.created_at, tweet.text)
                result[tweet.id] = tweet_info

                # print("\n{}[{}]:\n[{}]\n".format(
                #    tweet.id,
                #    tweet.created_at,
                #    tweet.text
                # ))
        except:
            print("Unexpected error[{}]: {}".format(
                current_time,
                sys.exc_info()[0]
            ))

        return result

    def update_db_file(self, id):
        with open(TWEET_IDS, 'a') as f:
            f.write(str(id) + "\n")

    def get_current_tweet_ids(self):
        tweet_ids = set()
        with open(TWEET_IDS) as f:
            lines = f.readlines()
            for line in lines:
                tweet_ids.add(int(line))

        return tweet_ids

    def process_tweets(self, tweets):
        current_tweet_ids = self.get_current_tweet_ids()
        for id, tweet in tweets.items():
            # print("{} => {}".format(
            #    id, tweet.content
            # ))

            if id not in current_tweet_ids:
                # Send to pubsub and update file.
                data = json.dumps(tweet.get_tweet_dict()).encode('utf-8')
                print(data)
                self.pubsub_client.publish_message(data)
                self.update_db_file(id)

    def run(self):
        while True:
            tweets = self.get_recent_fpl_tweets_upate()
            if len(tweets) > 0:
                self.process_tweets(tweets)
            sleep(10 * 60)


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
    description = 'FPL Updates'
    parser = argparse.ArgumentParser(usage=usage, description=description)
    parser.add_argument("-c", "--config", help="Configuration file",
                        required=True)
    parser.add_argument("--debug", help="Enable verbose logging",
                        action='store_true', required=False)
    parser.set_defaults(debug=False)

    args = parser.parse_args()

    config = parse_config_file(args.config)
    twitterConfig = config['twitterbot']
    gcpPubSubConfig = config['gcpPubSub']

    tweet_client = tweepy.Client(bearer_token=twitterConfig['apiBearerToken'])
    pubsub_client = GcpPubSubClient(
            project_id=gcpPubSubConfig['projectId'],
            topic_id=gcpPubSubConfig['publishId'])

    fpl_updates = FPLUpdates(tweet_client, pubsub_client)
    fpl_updates.start()
    fpl_updates.join()


if __name__ == "__main__":
    main()
