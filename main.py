from modules.logging_config import set_logging
import logging
from discord_bot.bot import Custom_Client
set_logging()

if __name__ == "__main__":
    client = Custom_Client()
    client.run()