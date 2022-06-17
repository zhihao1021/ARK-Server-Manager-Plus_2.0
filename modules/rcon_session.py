from queue import Queue
from rcon import Client

from modules import Thread

class Rcon_S():
    def __init__(
        self,
        address: str,
        port: int,
        passwd: str | None,
        timeout: int=60,
    ) -> None:
        self.in_queue = Queue()
    print