import logging
from modules.config import Config, _Ark_Server
from modules.queue import Queue
from modules.threading import Thread
from rcon.source import Client
from subprocess import Popen, PIPE, DEVNULL
from time import time, sleep
from typing import Optional, Union

logger = logging.getLogger("main")

_WHILE_SLEEP = 0.2
_TAG_LIST = ["Discord", "Web", "System"]
DISCORD = 0
WEB = 1
SYSTEM = 2

def tag_verify(tag: int) -> bool:
    """
    驗證發起者識別標籤。

    tag: :class:`int`
        發起者識別標籤
    
    return: :class:`bool`
    """
    return tag in range(len(_TAG_LIST))

def _text_retouch(text: str):
    if text == "": return None
    while text[0] == " ":
        text = text[1:]
        if text == "": return None
    while text[-1] == " ":
        text = text[:-1]
        if text == "": return None
    return text

def _text_verify(text: str, ban_dict: dict):
    if len(ban_dict["startswith"]) != 0:
        if text.startswith(tuple(ban_dict["startswith"])): return False
    for string in  len(ban_dict["include"]):
        if string in text: return False
    if len(ban_dict["endswith"]) != 0:
        if text.endswith(tuple(ban_dict["endswith"])): return False
    return True

def _process_info(name: str="") -> list | None:
    raw_info = Popen(f"wmic process where (name=\"{name}\") get name, executablepath, processid", shell=False, stdout=PIPE, stderr=DEVNULL).stdout.read().decode("utf-8").split("\r\r\n")[:-2]
    if "ExecutablePath" in raw_info[0] and "Name" in raw_info[0] and "ProcessId" in raw_info[0]:
        s_path = raw_info[0].find("ExecutablePath")
        s_name = raw_info[0].find("Name")
        s_pid = raw_info[0].find("ProcessId")
        result = []
        for i in range(1, len(raw_info)):
            if raw_info[i][s_pid:].replace(" ", "") != "":
                result.append(
                    {
                        "Path": raw_info[i][s_path:s_name - 2],
                        "Name": raw_info[i][s_name:s_pid - 2],
                        "PID": int(raw_info[i][s_pid:].replace(" ", "")),
                    }
                )
        return result
    else:
        return None

def _ark_is_alive(path: str) -> bool:
    alive_list = _process_info("ShooterGameServer.exe")
    for alive_process in alive_list:
        if path in alive_process["Path"]:
            return True
    return False

class Rcon_Session():
    """
    背景處理RCON指令。
    """
    def __init__(
        self,
        num: int
    ) -> None:
        """
        初始化`Rcon_Session()`
        
        num: :class:`int`
            伺服器資料編號

        return: :class:`None`
        """
        self.in_queue = Queue()
        self.queues: list[Queue] = []
        for _ in _TAG_LIST:
            self.queues.append(Queue())

        self.rcon_alive = False
        self.server_alive = False
        server_config: _Ark_Server = Config.servers[num]
        session_thread = Thread(target=self._session, name=f"RCON_{server_config.display_name}", args=(server_config,))
        session_thread.start()
        Config.servers[num].rcon_update(self)

    def add(
        self,
        command: str,
        tag: int,
        args: Optional[dict]=None
    ) -> None:
        """
        新增指令至執行佇列。
        
        command: :class:`str`
            欲新增的指令。
        tag: :class:`int`
            發起者識別標籤。
        args: :class:`dict`
            附加自訂參數。

        return: :class:`None`
        """
        if not tag_verify(tag):
            return None
        self.in_queue.put(
            {
                "command": command,
                "tag": tag,
                "args": args
            }
        )
        """
        args:
        {
            "type": "",
            "target": 0
        }
        """

    def get(
        self,
        tag: int
    ) -> Union[dict, None]:
        """
        取得指令輸出結果。
        
        tag: :class:`int`
            發起者識別標籤。

        return: :class:`dict | None`
        """
        if not tag_verify(tag):
            return None
        target_queue = self.queues[tag]
        if target_queue.empty():
            return None
        return target_queue.get()
    
    def _session(
        self,
        server_config: _Ark_Server
    ):
        config = server_config.rcon
        while True:
            try:
                self.in_queue.clear()
                with Client(
                    host=config.address,
                    port=config.port,
                    timeout=config.timeout,
                    passwd=config.password
                ) as client:
                    self.rcon_alive = True
                    self.server_alive = True
                    logger.warning("RCON Connected!")
                    while True:
                        if not self.in_queue.empty():
                            requests = self.in_queue.get()
                            command = requests["command"]
                            logger.info(f"From:{_TAG_LIST[tag]} Receive Command:{command}")
                            reply = client.run(command)
                            requests["reply"] = reply
                            tag = requests["tag"]
                            del requests["tag"]
                            self.queues[tag].put(requests)
                            logger.info(f"From:{_TAG_LIST[tag]} {command} Reply:{reply}")

                        # 取得聊天訊息
                        chat_message = client.run("GetChat")
                        if "Server received, But no response!!" in chat_message:
                            continue
                        # 分割訊息
                        chat_message_list = chat_message.split("\n")
                        for message in chat_message_list:
                            # 轉錄訊息
                            message = _text_retouch(message)
                            if message == None:
                                continue
                            logger.info(message)
                            if _text_verify(message, Config.other_setting.m_filter_tables[config.m_filter]):
                                # 修飾訊息
                                if message.startswith("部落"):
                                    tribe = message[2:message.find(", ID ")]
                                    if message.find("\">") != -1:
                                        message = message[message.find("\">")+2:-4]
                                    else:
                                        message = message.split(": ")[2][: -1]
                                        message = message.replace("部落成員", "")
                                        message = message.replace("你的部落", "")
                                    message = _text_retouch(message)
                                    if message == None:
                                        continue
                                    message = f"<{tribe}>{message}"
                                # 送出訊息
                                self.queues[DISCORD].put(
                                    {
                                        "reply": f"[{server_config.display_name}]{message}",
                                        "args": {
                                            "type": "chat",
                                            "target": server_config.discord.channel
                                        }
                                    }
                                )
                        sleep(_WHILE_SLEEP)
            except SystemExit:
                raise SystemExit
            except:
                try:
                    # 閃斷測試
                    sleep(10)
                    with Client(
                        host=config.address,
                        port=config.port,
                        timeout=config.timeout,
                        passwd=config.password
                    ) as client:
                        client.run("")
                except SystemExit:
                    raise SystemExit
                except:
                    self.rcon_alive = False
                    logger.warning("RCON Disconnected!")
                    while True:
                        try:
                            if _ark_is_alive(server_config.dir_path) and not self.server_alive:
                                self.server_alive = True
                                logger.warning("Server Up!")
                            # 嘗試重連
                            with Client(
                                host=config.address,
                                port=config.port,
                                timeout=config.timeout,
                                passwd=config.password
                            ) as client:
                                client.run("")
                                break
                        except SystemExit:
                            raise SystemExit
                        except:
                            if not _ark_is_alive(server_config.dir_path) and self.server_alive:
                                self.server_alive = False
                                logger.warning("Server Down!")
                        sleep(_WHILE_SLEEP)

# if (remove_message(conv_string)): 
# if conv_string.startswith("部落"):
#     tribe = string[2:string.find(", ID ")]
#     if string.find("\">") != -1: string = string[string.find("\">") + 2:-4]
#     else: string = string.split(": ")[2][:-1]
#     if conv_string.startswith("部落成員 "): string = string[5:]
#     if conv_string.startswith("你的部落"): string = string[4:]
#     string = f"<{tribe}>{string}"
# response.put(
#     {
#         "type": "chat",
#         "content": string
#     }
# )