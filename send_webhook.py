import pathlib
from os import getenv

from dotenv import load_dotenv
from mattermostdriver import Driver

dotenv_path = pathlib.Path(".") / ".env"
load_dotenv(dotenv_path)

url = getenv("URL")
token = getenv("TOKEN")
channel_id = getenv("CHANNEL_ID")
login_id = getenv("LOGIN_ID")

if url is None:
    raise ValueError("URL is not set")
if token is None:
    raise ValueError("TOKEN is not set")
if channel_id is None:
    raise ValueError("CHANNEL_ID is not set")
if login_id is None:
    raise ValueError("LOGIN_ID is not set")

# Mattermost Driver Setting
md = Driver(
    {
        "url": url,
        "login_id": login_id,
        "token": token,
        "scheme": "https",
        "port": 443,
        "veryfy": False,
    }
)


# mattermostへのログイン処理
md.login()

# チャネルへのメッセージ投稿
md.posts.create_post(options={"channel_id": channel_id, "message": "**post** message"})

# mattermostへのログアウト処理
md.logout()
