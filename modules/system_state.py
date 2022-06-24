from modules.json import Json
from modules.threading import Thread
from time import sleep, time
import psutil

class State:
    cpu_percent: float = 0
    ram_percent: float = 0
    upload_speed: float = 0
    download_speed: float = 0
    config: dict = {}
    request_config: str = ""

    @classmethod
    def update(self):
        self.cpu_percent = psutil.cpu_percent()
        self.ram_percent = psutil.virtual_memory().percent
        start_time = time()
        start_net_io = psutil.net_io_counters()
        sleep(1)
        end_time = time()
        end_net_io = psutil.net_io_counters()
        self.upload_speed = (end_net_io.bytes_sent - start_net_io.bytes_sent) / (2 * (end_time - start_time))
        self.download_speed = (end_net_io.bytes_recv - start_net_io.bytes_recv) / (2 * (end_time - start_time))
        self.config = {
            "cpu_percent": self.cpu_percent,
            "ram_percent": self.ram_percent,
            "upload_speed": self.upload_speed,
            "download_speed": self.download_speed,
        }
        self.request_config = Json.dumps(self.config)


def auto_update():
    while True:
        State.update()

auto_update_thread = Thread(target=auto_update, name="Config_Auto_Update")
auto_update_thread.start()