from discord_bot.bot import Custom_Client
import logging
from modules.config import Config
from modules.logging_config import set_logging
from modules.threading import Thread
import threading
from time import sleep
threading.active_count
set_logging()

logger = logging.getLogger("main")

while Config.readied == None: sleep(0.1)
if Config.readied == False:
    input("Press any key to exit...")
    exit()

if __name__ == "__main__":
    client = Custom_Client()

    discord_thread = Thread(target=client.run, name="Discord_Bot")
    discord_thread.start()
    while True:
        logger.debug(f"Thread:{''.join([thread.name for thread in threading.enumerate()])}")
        sleep(1)