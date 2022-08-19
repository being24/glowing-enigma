import pathlib
from datetime import datetime, timedelta
from os import getenv
from typing import List
from zoneinfo import ZoneInfo

import google.auth
import googleapiclient.discovery
from dotenv import load_dotenv
from dataclasses import dataclass


@dataclass
class GoogleCalendarData:
    start: datetime
    end: datetime
    summary: str
    organizer: str
    schedule_type: str
    timezone: ZoneInfo


class GoogleCalendar:
    def __init__(self):
        token_path = list(pathlib.Path(__file__).parent.glob("axial*.json"))[0]
        # Set scopes
        SCOPES = ["https://www.googleapis.com/auth/calendar"]
        # Load credentials from json file
        google_api_credential = google.auth.load_credentials_from_file(token_path, SCOPES)[0]
        # Create service object
        self.service = googleapiclient.discovery.build("calendar", "v3", credentials=google_api_credential)

    def get_calendar(
        self, calendarId: str, timeMin: str, timeMax: str, maxResults: int = 250, orderBy: str = "startTime"
    ) -> List[GoogleCalendarData]:
        """googleAPIを使用して条件に合うデータを取得する関数

        Args:
            calendarId (str): カレンダーのID
            timeMin (str): 取得するデータの開始時間
            timeMax (str): 取得するデータの終了時間
            maxResults (int, optional): 最大取得数. Defaults to 250.
            orderBy (str, optional): 並べ替えのオプション. Defaults to "startTime".

        Returns:
            List[GoogleCalendarData]: 取得したデータのリスト
        """

        event_list = (
            self.service.events()
            .list(
                calendarId=calendarId,
                timeMin=timeMin,
                timeMax=timeMax,
                maxResults=maxResults,
                singleEvents=True,
                orderBy=orderBy,
            )
            .execute()
        )
        calender_timezone = ZoneInfo(event_list["timeZone"])

        # ③イベントの開始時刻、終了時刻、概要を取得する
        events = event_list.get("items", [])
        formatted_events: List[GoogleCalendarData] = []

        for event in events:
            if "date" in event["start"].keys():
                start = datetime.strptime(event["start"]["date"], "%Y-%m-%d")
                start = start.replace(tzinfo=calender_timezone)
                end = datetime.strptime(event["end"]["date"], "%Y-%m-%d")
                end = end.replace(tzinfo=calender_timezone)
                schedule_type = "all_day"
                timezone = calender_timezone
            else:
                start = datetime.strptime(event["start"]["dateTime"], "%Y-%m-%dT%H:%M:%S%z")
                end = datetime.strptime(event["end"]["dateTime"], "%Y-%m-%dT%H:%M:%S%z")
                schedule_type = "time_limited"
                timezone = calender_timezone
            summary = event["summary"]
            organizer = event["organizer"]["email"]

            formatted_events.append(
                GoogleCalendarData(
                    start=start,
                    end=end,
                    summary=summary,
                    organizer=organizer,
                    schedule_type=schedule_type,
                    timezone=timezone,
                )
            )
        return formatted_events

    def get_next_week_events(self, calendar_id: str) -> List[GoogleCalendarData]:
        """次週のイベントを取得する関数

        Args:
            calendar_id (str): カレンダーのID

        Returns:
            List[GoogleCalendarData]: 取得したデータのリスト
        """
        # 現在時刻を取得
        now = datetime.now(local_timezone)

        # 次の月曜日の正子を取得
        next_monday = now + timedelta(days=(7 - now.weekday()))
        next_monday = next_monday.replace(hour=0, minute=0, second=0, microsecond=0)

        # 次の次の月曜日の正子を取得
        after_next_monday = next_monday + timedelta(days=7)

        # 次の月曜日から次の次の月曜日までのイベントを取得
        events = self.get_calendar(
            calendarId=calendar_id,
            timeMin=self.return_shaped_datetime(next_monday),
            timeMax=self.return_shaped_datetime(after_next_monday),
        )
        return events

    def get_next_day_events(self, calendar_id: str) -> List[GoogleCalendarData]:
        """次日のイベントを取得する関数

        Args:
            calendar_id (str): カレンダーのID

        Returns:
            List[GoogleCalendarData]:
        """

        # 現在時刻を取得
        now = datetime.now(local_timezone)

        # 次の日の正子を取得
        next_day = now + timedelta(days=1)
        next_day = next_day.replace(hour=0, minute=0, second=0, microsecond=0)

        # 次の次の日の正子を取得
        after_next_day = next_day + timedelta(days=1)

        # 次の日から次の次の日までのイベントを取得
        events = self.get_calendar(
            calendarId=calendar_id,
            timeMin=self.return_shaped_datetime(next_day),
            timeMax=self.return_shaped_datetime(after_next_day),
        )
        return events

    def get_events(self, calendar_id: str, maxResults: int = 10) -> List[GoogleCalendarData]:
        now = datetime.now(local_timezone)
        now_shaped = self.return_shaped_datetime(now)

        tg_time = now + timedelta(weeks=2)
        tg_time_shaped = self.return_shaped_datetime(tg_time)

        events = self.get_calendar(
            calendarId=calendar_id, timeMin=now_shaped, timeMax=tg_time_shaped, maxResults=maxResults
        )

        return events

    def return_shaped_datetime(self, time: datetime) -> str:
        """datetime型からgoogleAPIが受け取る形に変換する

        Args:
            time (datetime): 変換したいdatetime

        Returns:
            str: 変換後のdatetime
        """
        return time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def show_got_data(self, events: List[GoogleCalendarData]):
        """取得したデータを表示する関数

        Args:
            events (List[GoogleCalendarData]): 取得したデータのリスト
        """
        print(f"イベント{len(events)}件")
        for event in events:
            if event.schedule_type == "all_day":
                start_time = event.start.strftime("%Y/%m/%d")
                end_time = "All Day"
                summary = event.summary
                organizer = event.organizer
                timezone = event.timezone
            else:
                start_time = event.start.strftime("%Y/%m/%d %H:%M")
                end_time = event.end.strftime("%Y/%m/%d %H:%M")
                summary = event.summary
                organizer = event.organizer
                timezone = event.timezone
            print(f"{start_time} {end_time} {summary} {organizer} {timezone}")


if __name__ == "__main__":
    google_calender = GoogleCalendar()

    dotenv_path = pathlib.Path(".") / ".env"
    load_dotenv(dotenv_path)

    calendar_id = getenv("CALENDAR_ID")
    if calendar_id is None:
        raise ValueError("CALENDAR_ID is not set")

    local_timezone = ZoneInfo("localtime")

    events = google_calender.get_events(calendar_id)
    google_calender.show_got_data(events)
