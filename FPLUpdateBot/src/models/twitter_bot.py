import datetime
import json
import pytz
import tweepy

from time import sleep
from threading import Thread
from models.logger import Logger
log = Logger.getInstance().getLogger()

# TWEET_FIELDS = ['context_annotations', 'created_at']
TWEET_FIELDS = ['created_at']
MAX_TWEETS_PER_QUERY = 10

# TWEET_QUERY = 'from:Fpl_Updates -is:retweet'
TWEET_QUERY = ("from:{} -is:retweet")
TWEET_IDS = 'tweet_id.db'
USER_ID = "Fpl_Updates"

DEFAULT_TIMEZONE = "America/Los_Angeles"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

DEFAULT_TIME_M = (5 * 60)


class TweetInfo(object):

    def __init__(self, msg_type, id, timestamp, content):
        self.id = id
        self.timestamp = timestamp
        self.content = content
        self.use_as_is = False
        self.msg_type = msg_type

    def set_use_as_is(self, use_as_is=False):
        self.use_as_is = use_as_is

    def get_tweet_dict(self):
        return ({
                "msg_type": self.msg_type,
                # "timestamp": self.timestamp,
                "use_as_is": self.use_as_is,
                "tweet_id": self.id,
                "content": self.content
                })


class TwitterBot(Thread):

    def __init__(self,
                 msg_type,
                 lock,
                 twitter_bearer_token,
                 pubsub_client,
                 twitter_id=USER_ID,
                 tweet_delay=DEFAULT_TIME_M,
                 use_as_is=False,
                 max_tweets=MAX_TWEETS_PER_QUERY,
                 tweet_fields=TWEET_FIELDS,
                 timezone=DEFAULT_TIMEZONE,
                 tweets_id_db=TWEET_IDS):
        # Call the Thread class's init function
        Thread.__init__(self)
        self.setDaemon(True)
        self.msg_type = msg_type
        self.lock = lock
        self.client = tweepy.Client(bearer_token=twitter_bearer_token)
        self.pubsub_client = pubsub_client
        self.twitter_id = twitter_id
        self.tweet_query = TWEET_QUERY.format(twitter_id)
        self.max_tweets = max_tweets
        self.tweet_fields = tweet_fields
        self.timezone = timezone
        self.tweet_delay = tweet_delay
        self.use_as_is = use_as_is
        self.tweets_id_db = tweets_id_db

    def get_recent_tweets(self):
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

            if tweets is None or tweets.data is None:
                return result

            now = datetime.datetime.now()
            log.info("Successfully returned {} tweets at {} from {}".format(
                len(tweets.data),
                current_time,
                self.twitter_id
            ))

            for tweet in tweets.data:
                tweet_info = \
                        TweetInfo(self.msg_type, tweet.id, 
                                  tweet.created_at, tweet.text)
                tweet_info.set_use_as_is(self.use_as_is)
                result[tweet.id] = tweet_info

                log.debug("\n{}[{}]:\n[{}]\n".format(
                   tweet.id,
                   tweet.created_at,
                   tweet.text
                ))
        except BaseException as ex:
            log.info("Unexpected error[{}]: {}".format(
                current_time, ex
            ))

        return result

    def update_db_file(self, id):
        self.lock.acquire()
        with open(self.tweets_id_db, 'a') as f:
            f.write(str(id) + "\n")
        self.lock.release()

    def get_current_tweet_ids(self):
        self.lock.acquire()
        tweet_ids = set()
        with open(self.tweets_id_db) as f:
            lines = f.readlines()
            for line in lines:
                tweet_ids.add(int(line))

        self.lock.release()
        return tweet_ids

    def process_tweets(self, tweets):
        current_tweet_ids = self.get_current_tweet_ids()
        for id, tweet in tweets.items():
            log.debug("{} => {}".format(
               id, tweet.content
            ))

            if id not in current_tweet_ids:
                # Send to pubsub and update file.
                data = json.dumps(tweet.get_tweet_dict()).encode('utf-8')
                log.info(data)
                self.pubsub_client.publish_message(data)
                self.update_db_file(id)

    def run(self):
        while True:
            tweets = self.get_recent_tweets()
            if tweets and len(tweets) > 0:
                self.process_tweets(tweets)
            sleep(self.tweet_delay)
