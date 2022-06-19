import praw
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


def postToReddit(title, path):
    if not os.getenv("FROM_GITHUB_ACTION"):
        print("not running from github action, will not post")
        return
    reddit.subreddit("mlbVis").submit_image(title, path)
