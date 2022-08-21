import pathlib
from os import getenv

from dotenv import load_dotenv
from mattermostdriver import Driver


class Mattermost:
    def __init__(self, url: str, channel_id: str, bot_token: str):
        """mattermostのデータを取得するクラスのコンストラクタ

        Args:
            url (str): mattermostのURL
            channel_id (str): mattermostのチャンネルID
            bot_token (str): mattermostのbotのトークン
        """
        self.url = url
        self.channel_id = channel_id
        self.bot_token = bot_token

        self.driver = Driver(
            {
                "url": url,
                "token": bot_token,
                "scheme": "https",
                "port": 443,
                "veryfy": False,
            }
        )

        self.driver.login()

    def __del__(self):
        self.driver.logout()

    def post(self, message: str):
        """mattermostにメッセージを投稿する関数

        Args:
            message (str): 投稿するメッセージ
        """
        self.driver.posts.create_post(options={"channel_id": self.channel_id, "message": message})

    def attached_post(self, message: str, attachments: list[dict]):
        self.driver.client.make_request(
            "post",
            "/posts",
            options={"channel_id": self.channel_id, "message": message, "props": {"attachments": attachments}},
        )


if __name__ == "__main__":
    dotenv_path = pathlib.Path(".") / ".env"
    load_dotenv(dotenv_path)

    url = getenv("URL")
    channel_id = getenv("CHANNEL_ID")
    bot_token = getenv("BOT_TOKEN")

    if url is None:
        raise ValueError("URL is not set")
    if channel_id is None:
        raise ValueError("CHANNEL_ID is not set")
    if bot_token is None:
        raise ValueError("BOT_TOKEN is not set")

    driver = Mattermost(url, channel_id, bot_token)
    attachments = [
        {
            "color": "#87CEEB",
            "text": "message attachments",
            "title": "This is title",
            "title_link": "https://github.com/mattermost",
        },
        {
            "color": "#87CEEB",
            "text": "message attachments",
            "title": "This is title2",
            "title_link": "https://github.com/mattermost",
        },
    ]
    driver.attached_post("Hello World\n---", attachments)
