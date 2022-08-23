import pathlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from os import getenv
from typing import List
from venv import create
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from mattermostdriver import Driver


@dataclass
class MattermostPostData:
    post_id: str
    created_at: datetime
    user_id: str
    channel_id: str
    message: str


class Mattermost:
    def __init__(self, url: str, bot_token: str, local_timezone: ZoneInfo):
        """mattermostのデータを取得するクラスのコンストラクタ

        Args:
            url (str): mattermostのURL
            channel_id (str): mattermostのチャンネルID
            bot_token (str): mattermostのbotのトークン
        """
        self.url = url
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

        self.local_timezone = local_timezone

        self.driver.login()

    def __del__(self):
        self.driver.logout()

    def post(self, channel_id: str, message: str):
        """mattermostにメッセージを投稿する関数

        Args:
            channel_id (str): 投稿するチャンネルID
            message (str): 投稿するメッセージ
        """
        self.driver.posts.create_post(options={"channel_id": channel_id, "message": message})

    def attached_post(self, channel_id: str, message: str, attachments: list[dict]):
        """mattermostにattachmentsを持つメッセージを投稿する関数

        Args:
            channel_id (str): 投稿するチャンネルID
            message (str): 投稿するメッセージ
            attachments (list[dict]): 投稿するattachmentsのリスト
        """
        self.driver.client.make_request(
            "post",
            "/posts",
            options={"channel_id": channel_id, "message": message, "props": {"attachments": attachments}},
        )

    def get_cannel_posts(self, channel_id: str) -> List[MattermostPostData]:
        channel_data = self.driver.posts.get_posts_for_channel(channel_id)
        if "status_code" in channel_data.keys():
            return []

        post_list = []

        for post in channel_data["posts"].values():
            create_at = datetime.fromtimestamp(post["create_at"] / 1000, self.local_timezone)
            # post_data = MattermostPostData(
            post = MattermostPostData(
                post_id=post["id"],
                created_at=create_at,
                user_id=post["user_id"],
                channel_id=channel_id,
                message=post["message"],
            )
            post_list.append(post)

        post_list = sorted(post_list, key=lambda x: x.created_at)

        return post_list

    @staticmethod
    def return_user_id_list(post_list: List[MattermostPostData], user_id: str) -> List[MattermostPostData]:
        """投稿者のIDがuser_idのものを返す関数

        Args:
            post_list (List[MattermostPostData]): 投稿のリスト
            user_id (str): 投稿者のID

        Returns:
            List[MattermostPostData]: 投稿のリスト
        """
        return [post for post in post_list if post.user_id == user_id]

    @staticmethod
    def return_before_post(post_list: List[MattermostPostData], before_date: datetime) -> List[MattermostPostData]:
        """投稿日時がbefore_date以前のものを返す関数

        Args:
            post_list (List[MattermostPostData]): 投稿のリスト
            before_date (datetime): 削除する日時

        Returns:
            List[MattermostPostData]: 投稿のリスト
        """
        return [post for post in post_list if post.created_at < before_date]

    def return_shift_datetime(self, now: datetime, before_date: int = -1) -> datetime:
        """指定した日数を移動させた日時を返す関数

        Args:
            now (datetime): 現在の日時
            before_date (int, optional): ずらす日数. Defaults to -1.

        Returns:
            datetime: 指定した日数を経過した日時
        """
        now = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return now + timedelta(days=before_date)

    def return_everyday_posts(self, now: datetime, channel_id: str, bot_id: str) -> List[MattermostPostData]:
        """削除対象の毎日の投稿を返す関数

        Args:
            now (datetime): 現在の日時
            channel_id (str): 取得するチャンネルID
            bot_id (str): 取得するbotのID

        Returns:
            List[MattermostPostData]: 投稿のリスト
        """
        post_list = self.get_cannel_posts(channel_id)

        tg_list = self.return_user_id_list(post_list, bot_id)

        # 毎日の投稿を消す
        del_list_one = self.return_before_post(tg_list, self.return_shift_datetime(now, -1))
        del_list_one = [post for post in del_list_one if "this week" not in post.message]

        return del_list_one

    def return_week_day_posts(self, now: datetime, channel_id: str, bot_id: str) -> List[MattermostPostData]:
        """削除対象の毎週の投稿を返す関数

        Args:
            now (datetime): 現在の日時
            channel_id (str): 取得するチャンネルID
            bot_id (str): 取得するbotのID

        Returns:
            List[MattermostPostData]: 投稿のリスト
        """
        post_list = self.get_cannel_posts(channel_id)

        tg_list = self.return_user_id_list(post_list, bot_id)

        del_list_seven = self.return_before_post(tg_list, self.return_shift_datetime(now, -6))
        del_list_seven = [post for post in del_list_seven if "this week" in post.message]

        return del_list_seven

    def delete_posts(self, post_list: List[MattermostPostData]):
        """投稿を削除する関数

        Args:
            post_list (List[MattermostPostData]): 削除する投稿のリスト
        """
        for post in post_list:
            self.driver.posts.delete_post(post.post_id)


if __name__ == "__main__":
    dotenv_path = pathlib.Path(".") / ".env"
    load_dotenv(dotenv_path)

    url = getenv("URL")
    channel_id = getenv("CHANNEL_ID")
    bot_token = getenv("BOT_TOKEN")
    bot_id = getenv("BOT_ID")

    if url is None:
        raise ValueError("URL is not set")
    if channel_id is None:
        raise ValueError("CHANNEL_ID is not set")
    if bot_token is None:
        raise ValueError("BOT_TOKEN is not set")
    if bot_id is None:
        raise ValueError("BOT_ID is not set")

    local_timezone = ZoneInfo("Asia/Tokyo")

    now = datetime.now(local_timezone)

    driver = Mattermost(url, bot_token, local_timezone)
    # attachments = [
    #     {
    #         "color": "#87CEEB",
    #         "text": "message attachments",
    #         "title": "This is title",
    #         "title_link": "https://github.com/mattermost",
    #     },
    #     {
    #         "color": "#87CEEB",
    #         "text": "message attachments",
    #         "title": "This is title2",
    #         "title_link": "https://github.com/mattermost",
    #     },
    # ]
    # driver.attached_post(channel_id, "Hello World\n---", attachments)

    del_list_one = driver.return_everyday_posts(now, channel_id, bot_id)
    print(f"{len(del_list_one)} posts will be deleted")

    del_list_seven = driver.return_week_day_posts(now, channel_id, bot_id)
    print(f"{len(del_list_seven)} posts will be deleted")
