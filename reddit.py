import datetime
import praw


def pretty_date(submission):
    s_time = submission.created_utc
    return str(datetime.datetime.fromtimestamp(s_time))


def get_subreddit_cat(subreddit, cat):
    if cat == "controversial":
        return subreddit.controversial
    elif cat == "new":
        return subreddit.new
    elif cat == "rising":
        return subreddit.rising
    elif cat == "top":
        return subreddit.top
    else:
        return subreddit.hot

with open("reddit.keys") as f:
    content = f.readlines()

content = [x.strip() for x in content]

reddit = praw.Reddit(client_id=content[0],
                     client_secret=content[1],
                     user_agent=content[2])
