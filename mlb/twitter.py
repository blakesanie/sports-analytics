import tweepy
import os

try:
    from dotenv import load_dotenv

    # load env vars from .env file if package and file exist, otherwise skip (secrets already set in server env)
    load_dotenv()
except ImportError:
    pass

auth = tweepy.OAuthHandler(
    os.getenv("TWITTER_V1_API_KEY"), os.getenv("TWITTER_V1_API_KEY_SECRET")
)
auth.set_access_token(
    os.getenv("TWITTER_V1_ACCESS_TOKEN"), os.getenv("TWITTER_V1_ACCESS_TOKEN_SECRET")
)
api = tweepy.API(auth)


def postTweetWithFilenames(text, filenames):
    media_ids = [api.media_upload(filename).media_id for filename in filenames]
    post_result = api.update_status(status=text, media_ids=media_ids)
