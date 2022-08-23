import pathlib
from datetime import datetime
from os import getenv
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

import google_calender
import mattermost_driver
from google_calender import GoogleCalendarData


def create_attachments(events: list[GoogleCalendarData]) -> list[dict]:
    """googleカレンダーから取得したイベントをmattermostに投稿するためのattachmentsを作成する関数

    Args:
        events (list[GoogleCalendarData]): googleカレンダーから取得したイベントのリスト

    Returns:
        list[dict]: attachmentsのリスト
    """
    attachments = []
    for event in events:
        if event.schedule_type == "all_day":
            msg = f"{event.start.strftime('%m/%d')} all_day"
        else:
            msg = (
                f"{event.start.strftime('%m/%d')} from {event.start.strftime('%H:%M')} to {event.end.strftime('%H:%M')}"
            )

        data = {
            "color": "#87CEEB",
            "text": f"{msg}",
            "title": f"{event.summary}",
            "title_link": f"{event.html_link}",
        }
        attachments.append(data)

    return attachments


if __name__ == "__main__":
    dotenv_path = pathlib.Path(".") / ".env"
    load_dotenv(dotenv_path)

    url = getenv("URL")
    channel_id = getenv("CHANNEL_ID")
    bot_token = getenv("BOT_TOKEN")
    calendar_id = getenv("CALENDAR_ID")
    bot_id = getenv("BOT_ID")

    if url is None:
        raise ValueError("URL is not set")
    if channel_id is None:
        raise ValueError("CHANNEL_ID is not set")
    if bot_token is None:
        raise ValueError("BOT_TOKEN is not set")
    if calendar_id is None:
        raise ValueError("CALENDAR_ID is not set")
    if bot_id is None:
        raise ValueError("BOT_ID is not set")

    token_paths = list(pathlib.Path(__file__).parent.glob("axial*.json"))
    if len(token_paths) == 0:
        raise FileNotFoundError("Token file not found")
    else:
        token_path = token_paths[0]

    local_timezone = ZoneInfo("Asia/Tokyo")

    gc = google_calender.GoogleCalendar(token_path, local_timezone)
    driver = mattermost_driver.Mattermost(url=url, bot_token=bot_token, local_timezone=local_timezone)

    now = datetime.now(local_timezone)

    # 今が日曜日の19時ならば
    if now.weekday() == 6 and now.hour == 19:

        del_list_week = driver.return_week_day_posts(now=now, channel_id=channel_id, bot_id=bot_id)
        driver.delete_posts(del_list_week)

        # 週間予定
        events = gc.get_next_week_events(calendar_id)

        if len(events) == 0:
            msg_header = "There is no events this week"
        else:
            msg_header = f"There is **{len(events)}** events this week"

        attachments = create_attachments(events)

        driver.attached_post(channel_id, f"{msg_header}\n---\n", attachments)

    # 今が7時ならば
    if now.hour == 10:
        del_list_one = driver.return_everyday_posts(now, channel_id, bot_id)
        driver.delete_posts(del_list_one)

        # 本日の予定
        events = gc.get_today_events(calendar_id)
        if len(events) == 0:
            msg_header = "There is no events today"
        else:
            msg_header = f"There is **{len(events)}** events today"

        attachments = create_attachments(events)

        driver.attached_post(channel_id, f"{msg_header}\n---\n", attachments)
