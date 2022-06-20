import praw
from praw.models import InlineImage
import os

try:
    from dotenv import load_dotenv

    # load env vars from .env file if package and file exist, otherwise skip (secrets already set in server env)
    load_dotenv()
except ImportError:
    pass

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_KEY"),
    client_secret=os.getenv("REDDIT_SECRET"),
    user_agent="script:com.blakesanie.mlbVis:v1.0.0 (by u/mlbVis)",
    username="mlbVis",
    password=os.getenv("REDDIT_PASSWORD"),
)


def postToReddit(message, path):
    if not os.getenv("FROM_GITHUB_ACTION"):
        print("not running from github action, will not post")
        return
    # image = InlineImage(path=path)
    # media = {"image1": image}
    # reddit.subreddit("mlbVis").submit(message[0], inline_media=media, selftext='\n\n'.join(message[1:]))
    reddit.subreddit("mlbVis").submit_image(" | ".join(message), path)
