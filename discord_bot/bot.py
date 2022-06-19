from discord import Message
from discord.client import Client
import logging
from modules.config import Config, _Ark_Server
from modules.rcon import Rcon_Session

logger = logging.getLogger("main")

def _search_config(channel_id: int):
    server_config: _Ark_Server
    for server_config in Config.servers:
        if channel_id == server_config.discord.chat_channel:
            return server_config
    return None

class Custom_Client(Client):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        # print([logger.getLogger(name) for name in logger.root.manager.loggerDict])
        self.first_connect = True

    async def on_ready(self):
        if self.first_connect:
            logger.warning("Discord Bot Connected!")
        else:
            logger.warning("Discord Bot Reonnected!")

    async def on_message(self, message: Message):
        if message.author == self.user: return
        if not _search_config(message.channel.id): return
        if Config.discord.admin_role not in [role.id for role in message.author.roles]: return
        content = message.content
        logger.info(f"[{message.channel.name}][{message.author.display_name}]{content}")
        if not content.startswith(Config.discord.prefixs): return
        for prefix in Config.discord.prefixs:
            if content.startswith(prefix):
                content = content[len(prefix):]
                break
        content_list = content.split(" ")
        if content_list[0] == "c":
            if content_list[1] == "start":
                pass
        
    
    async def on_disconnect(self):
        logger.warning("Discord Bot Disconnected!")

    def run(self, *args, **kwargs) -> None:
        return super().run(Config.discord.token, *args, **kwargs)

if __name__ == "__main__":
    client = Client()
    client.run()