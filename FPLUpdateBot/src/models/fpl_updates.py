import datetime
import json
import pytz
import tweepy
import sys

from time import sleep
from threading import Thread

# TWEET_FIELDS = ['context_annotations', 'created_at']
TWEET_FIELDS = ['created_at']
MAX_TWEETS_PER_QUERY = 10

# TWEET_QUERY = 'from:Fpl_Updates -is:retweet'
TWEET_QUERY = ("from:{} -is:retweet")
TWEET_IDS = 'tweet_id.db'
USER_ID = "Fpl_Updates"

DEFAULT_TIMEZONE = "America/Los_Angeles"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


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

    def __init__(self,
                 lock,
                 twitter_bearer_token,
                 pubsub_client,
                 twitter_id=USER_ID,
                 max_tweets=MAX_TWEETS_PER_QUERY,
                 tweet_fields=TWEET_FIELDS,
                 timezone=DEFAULT_TIMEZONE):
        # Call the Thread class's init function
        Thread.__init__(self)
        self.lock = lock
        self.client = tweepy.Client(bearer_token=twitter_bearer_token)
        self.pubsub_client = pubsub_client
        self.twitter_id = twitter_id
        self.tweet_query = TWEET_QUERY.format(twitter_id)
        self.max_tweets = max_tweets
        self.tweet_fields = tweet_fields
        self.timezone = timezone

    def get_recent_fpl_tweets_upate(self):
        result = dict()
        now = datetime.datetime.now()
        # current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        utc_now = pytz.utc.localize(now)
        pst_now = utc_now.astimezone(pytz.timezone(self.timezone))
        current_time = pst_now.strftime(TIME_FORMAT)

        try:
            tweets = self.client.search_recent_tweets(
                    query=self.tweet_query,
                    tweet_fields=self.tweet_fields,
                    max_results=self.max_tweets)

            now = datetime.datetime.now()
            print("Successfully returned {} tweets at {} from {}".format(
                len(tweets.data),
                current_time,
                self.twitter_id
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
        self.lock.acquire()
        with open(TWEET_IDS, 'a') as f:
            f.write(str(id) + "\n")
        self.lock.release()

    def get_current_tweet_ids(self):
        self.lock.acquire()
        tweet_ids = set()
        with open(TWEET_IDS) as f:
            lines = f.readlines()
            for line in lines:
                tweet_ids.add(int(line))

        self.lock.release()
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
            sleep(5 * 60)
