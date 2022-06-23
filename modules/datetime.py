from datetime import datetime, time, timedelta
from time import sleep
from typing import Union
from modules.config import Config

class My_Datetime:
    def now() -> datetime:
        """
        取得當前時間。
        
        return: :class:`datetime`
        """
        while not Config.updated: sleep(0.1)
        return datetime.now(Config.time_setting.time_zone).replace(tzinfo=None)

    def in_range(
        target: Union[str, time],
        delay: timedelta=timedelta(seconds=0),
        offset: timedelta=timedelta(minutes=-5),
        time_range: timedelta=timedelta(seconds=30)
    ) -> bool:
        """
        查看當前時間是否等於目標時間。

        target: :class:`str | time`
            當前所在時區。
        delay: :class:`timedelta`
            延遲(秒)。
        offset: :class:`timedelta`
            提前(分鐘)。
        time_range: :class:`timedelta`
            誤差範圍。
        
        return: :class:`bool`
        """
        if type(target) == str:
            target = time.fromisoformat(target)
        target.replace(tzinfo=None)
        now_time = My_Datetime.now()
        start_time = datetime.combine(now_time.date(), target) + delay + offset
        end_time = start_time + time_range
        return now_time >= start_time and now_time <= end_time
    
    def fileformat(timestamp: datetime=now()):
        return timestamp.replace(microsecond=0, tzinfo=None).isoformat().replace(":", "_")