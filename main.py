from discord_bot.bot import Custom_Client
import logging
from modules.config import Config
from modules.logging_config import set_logging
from modules.threading import Thread
from threading import current_thread
from time import sleep

set_logging()

logger = logging.getLogger("main")

while Config.readied == None: sleep(0.1)
if Config.readied == False:
    input("Press any key to exit...")
    exit()

if __name__ == "__main__":
    current_thread().name = "Discord_Bot"
    client = Custom_Client()
    client.run()