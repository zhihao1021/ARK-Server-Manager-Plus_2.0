from datetime import datetime, time, timedelta
from typing import Union
from modules.config import Config

class My_Datetime:
    def now() -> datetime:
        """
        取得當前時間。
        
        return: :class:`datetime`
        """
        return datetime.now(Config.time_setting.time_zone).replace(tzinfo=None)

    def in_range(
        target: Union[str, time],
        delay: timedelta=timedelta(seconds=0),
        time_range: timedelta=timedelta(seconds=5)
    ) -> bool:
        """
        查看當前時間是否等於目標時間。

        target: :class:`str | time`
            當前所在時區
        delay: :class:`timedelta`
            延遲
        time_range: :class:`timedelta`
            誤差範圍
        
        return: :class:`bool`
        """
        if type(target) == str:
            target = time.fromisoformat(target)
        target.replace(tzinfo=None)
        now_time = My_Datetime.now()
        start_time = datetime.combine(now_time.date(), target) + delay
        end_time = start_time + time_range
        return now_time >= start_time and now_time <= end_time