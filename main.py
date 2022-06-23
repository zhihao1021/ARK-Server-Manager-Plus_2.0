from discord_bot.bot import Custom_Client
import logging
from modules.config import Config, _Time_Data
from modules.datetime import My_Datetime
from modules.logging_config import set_logging
from modules.rcon import Rcon_Session, TAG_SYSTEM
from modules.threading import Thread
import psutil
from time import sleep
from web_console.console import Console

set_logging()

logger = logging.getLogger("main")

# 檢查設置檔。
while Config.readied == None: sleep(0.1)
if Config.readied == False:
    input("Press any key to exit...")
    exit()

def auto_save():
    """
    自動存檔計時。
    """
    timedata: _Time_Data
    while True:
        # 存檔
        for key in Config.time_setting.save_tables.keys():
            delay_i = 0
            for timedata in Config.time_setting.save_tables[key]:
                if not My_Datetime.in_range(timedata.time):
                    continue
                for server_config in Config.servers:
                    if server_config.save != key:
                        continue
                    rcon_session: Rcon_Session = server_config.rcon_session
                    rcon_session.save(TAG_SYSTEM, timedata.backup, Config.time_setting.save_delay * delay_i)
                    delay_i += 1
                while My_Datetime.in_range(timedata.time): sleep(0.5)
        # 重啟
        for key in Config.time_setting.restart_tables.keys():
            delay_i = 0
            for timedata in Config.time_setting.restart_tables[key]:
                if not My_Datetime.in_range(timedata.time):
                    continue
                for server_config in Config.servers:
                    if server_config.save != key:
                        continue
                    rcon_session: Rcon_Session = server_config.rcon_session
                    rcon_session.restart(TAG_SYSTEM, timedata.backup, Config.time_setting.save_delay * delay_i)
                    delay_i += 1
                while My_Datetime.in_range(timedata.time): sleep(0.5)
        sleep(3)
    


if __name__ == "__main__":
    logger.info("Version: 1.2.0")

    client = Custom_Client()
    console = Console()

    auto_save_thread = Thread(target=auto_save, name="Auto_Save")
    auto_save_thread.start()

    console_thread = Thread(target=console.run(), name="Web_Console")
    console_thread.start()

    discord_thread = Thread(target=client.run, name="Discord_Bot")
    discord_thread.start()

    BATTERY = psutil.sensors_battery()
    auto_save_thread = Thread()

    while True:

        if BATTERY != None:
            if BATTERY.percent < Config.other_setting.low_battery:
                for server_config in Config.servers:
                    rcon_session: Rcon_Session = server_config.rcon_session
                    rcon_session.stop(TAG_SYSTEM, backup=True, delay=3, reason=f"電池電量不足，剩餘{BATTERY.percent}%(Low battery, remaining{BATTERY.percent}%)")
        sleep(1)
        # logger.debug(f"Thread:{' '.join([thread.name for thread in threading.enumerate()])}")
        # sleep(10)