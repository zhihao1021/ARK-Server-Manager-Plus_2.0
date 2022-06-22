import logging
from modules.config import Config, _Ark_Server
from modules.datetime import My_Datetime
from modules.queue import Queue
from modules.threading import Thread
from os import system, makedirs, listdir
from os.path import join, isdir
from rcon.source import Client
from shutil import copyfile, copytree, rmtree
from subprocess import Popen, PIPE, DEVNULL
from time import sleep
from typing import Optional, Union

logger = logging.getLogger("main")

_WHILE_SLEEP = 0.2
_TAG_LIST = ["Discord", "Web", "System"]
TAG_DISCORD = 0
TAG_WEB = 1
TAG_SYSTEM = 2

_MODE_LIST = ["save", "stop", "restart"]
_MODE_LIST_ZH = ["儲存", "關閉", "重啟"]
MODE_SAVE = 0
MODE_STOP = 1
MODE_RESTART = 2

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
    for string in  ban_dict["include"]:
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
        num: int=-1
    ) -> None:
        """
        初始化`Rcon_Session()`
        
        num: :class:`int`
            伺服器資料編號

        return: :class:`None`
        """
        if Config.servers[num].rcon_session == None:
            self.in_queue = Queue()
            self.queues: list[Queue] = []
            for _ in _TAG_LIST:
                self.queues.append(Queue())

            self.rcon_alive = False
            self.server_alive = False
            self.server_first_connect = True
            self.server_config: _Ark_Server = Config.servers[num]
            session_thread = Thread(target=self._session, name=f"RCON_{self.server_config.display_name}")
            session_thread.start()
            Config.servers[num].rcon_update(self)

            self.save_thread = Thread()

    def add(
        self,
        command: str,
        tag: int,
        args: Optional[dict]={},
        reply: bool=True
    ) -> None:
        """
        新增指令至執行佇列。
        
        command: :class:`str`
            欲新增的指令。
        tag: :class:`int`
            發起者識別標籤。
        args: :class:`dict`
            附加自訂參數。
        reply: :class:`bool`
            是否回傳伺服器回覆內容。

        return: :class:`None`
        """
        if not tag_verify(tag):
            return None
        if not self.rcon_alive:
            if tag == TAG_DISCORD:
                self.queues[TAG_DISCORD].put(
                    {
                        "reply": f"[{self.server_config.display_name}]RCON 未連線，無法發送指令。",
                        "args": {
                            "type": "chat",
                            "target": self.server_config.discord.chat_channel
                        }
                    }
                )
            return
        logger.debug(f"Receive Command: {command}")
        self.in_queue.put(
            {
                "command": command,
                "tag": tag,
                "need_reply": reply,
                "args": args
            }
        )
        """
        Discord Args:
        args:
        {
            "type": "",   #chat, user_command
            "target": 0   #Target Channel
        }
        System Args:
        args:
        {
            "type": "",     #id_tag
            "content": ""   #Custom Content
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
        data = target_queue.get()
        logger.debug(f"Reply Command: {data}")
        return data
    
    def save(
        self,
        tag: int,
        backup: bool,
        delay: int=0,
        reason: str=""
    ) -> None:
        return self._save(tag, backup, MODE_SAVE, delay, reason)

    def stop(
        self,
        tag: int,
        backup: bool,
        delay: int=0,
        reason: str=""
    ) -> None:
        return self._save(tag, backup, MODE_STOP, delay, reason)
    
    def restart(
        self,
        tag: int,
        backup: bool,
        delay: int=0,
        reason: str=""
    ) -> None:
        return self._save(tag, backup, MODE_RESTART, delay, reason)

    def start(
        self,
        tag: int
    ) -> None:
        if self.server_alive:
            if tag == TAG_DISCORD:
                self.queues[TAG_DISCORD].put(
                    {
                        "reply": f"[{self.server_config.display_name}]伺服器已經啟動了。",
                        "args": {
                            "type": "chat",
                            "target": self.server_config.discord.chat_channel
                        }
                    }
                )
            return
        _cmd_path = join(self.server_config.dir_path, "ShooterGame\\Saved\\Config\\WindowsServer\\RunServer.cmd")
        with open(_cmd_path, mode="r", encoding="utf-8") as _cmd_file:
            command_content = _cmd_file.read()
            _cmd_file.close()
        location_s = command_content.find("?MultiHome=") + 11
        location_e = location_s + command_content[location_s:].find("?")
        original_config = f"?MultiHome={command_content[location_s:location_e]}"
        command_content = command_content.replace(original_config, "?MultiHome=0.0.0.0")
        with open(_cmd_path, mode="w", encoding="utf-8") as _cmd_file:
            _cmd_file.write(command_content)
            _cmd_file.close()
        system("start cmd /c \"" + _cmd_path + "\"")
        self.server_first_connect = True
    
    def clear(
        self,
        tag: int
    ) -> None:
        if not tag_verify(tag):
            return 
        self.in_queue.clear()
        if self.save_thread.is_alive():
            self.save_thread.stop()
        logger.warning(f"清除所有指令。(來自{_TAG_LIST[tag]})")
        if tag == TAG_DISCORD:
            self.queues[TAG_DISCORD].put(
                {
                    "reply": f"[{self.server_config.display_name}]已清除所有指令。",
                    "args": {
                        "type": "chat",
                        "target": self.server_config.discord.chat_channel
                    }
                }
            )
    
    def _save(
        self,
        tag: int,
        backup: bool,
        mode: int,
        delay: int,
        reason: str
    ) -> None:
        if not tag_verify(tag):
            return
        if self.rcon_alive and not self.save_thread.is_alive():
            self.save_thread = Thread(target=self._save_job, args=(tag, backup, mode, delay, reason), name=f"RCON_{self.server_config.display_name}_{_MODE_LIST[mode].upper()}")
            self.save_thread.start()
        elif tag == TAG_DISCORD:
            if not self.rcon_alive:
                self.queues[TAG_DISCORD].put(
                    {
                        "reply": f"[{self.server_config.display_name}]RCON 未連線，無法{_MODE_LIST_ZH[mode]}。",
                        "args": {
                            "type": "chat",
                            "target": self.server_config.discord.chat_channel
                        }
                    }
                )
            elif self.save_thread.is_alive():
                self.queues[TAG_DISCORD].put(
                    {
                        "reply": f"[{self.server_config.display_name}]已經正在{_MODE_LIST_ZH[mode]}中。",
                        "args": {
                            "type": "chat",
                            "target": self.server_config.discord.chat_channel
                        }
                    }
                )

    def _save_job(
        self,
        tag: int,
        backup: bool,
        mode: int,
        delay: int,
        reason: str
    ) -> None:
        logger.info(f"From:{_TAG_LIST[tag]} Receive Command:{_MODE_LIST[mode]} {delay} Reason:{reason}")
        def _rcon_test():
            if not self.rcon_alive:
                self.queues[TAG_DISCORD].put(
                    {
                        "reply": f"[{self.server_config.display_name}]儲存失敗: RCON失去連線。",
                        "args": {
                            "type": "chat",
                            "target": self.server_config.discord.chat_channel
                        }
                    }
                )
                logger.warning("儲存失敗: RCON失去連線。")
        if reason != "" and delay >= 1:
            ark_message = Config.other_setting.message[_MODE_LIST[mode]].replace('$TIME', str(delay))
            ark_message += f"\n原因:{reason}\nReason:{reason}"
            self.add(f"Broadcast {ark_message}", TAG_SYSTEM, reply=False)
            _discord_message = f"\n[{self.server_config.display_name}]".join(Config.other_setting.message[_MODE_LIST[mode]].replace("$TIME", str(delay)).split("\n"))
            _discord_message += f"\n[{self.server_config.display_name}]原因:{reason}\n[{self.server_config.display_name}]Reason:{reason}"
            self.queues[TAG_DISCORD].put(
                {
                    "reply": f"[{self.server_config.display_name}]{_discord_message}",
                    "args": {
                        "type": "chat",
                        "target": self.server_config.discord.chat_channel
                    }
                }
            )
            sleep(60)
            delay -= 1
        # 通知
        while delay > 0:
            _rcon_test()
            if (delay %5 == 0 and delay <= 30) or delay < 5:
                self.add(f"Broadcast {Config.other_setting.message[_MODE_LIST[mode]].replace('$TIME', str(delay))}", TAG_SYSTEM, reply=False)
                _discord_message = f"\n[{self.server_config.display_name}]".join(Config.other_setting.message[_MODE_LIST[mode]].replace("$TIME", str(delay)).split("\n"))
                self.queues[TAG_DISCORD].put(
                    {
                        "reply": f"[{self.server_config.display_name}]{_discord_message}",
                        "args": {
                            "type": "chat",
                            "target": self.server_config.discord.chat_channel
                        }
                    }
                )
            sleep(60)
            delay -= 1
        self.add(f"Broadcast {Config.other_setting.message['saving'].replace('$TIME', str(delay))}", TAG_SYSTEM, reply=False)
        _discord_message = f"\n[{self.server_config.display_name}]".join(Config.other_setting.message["saving"].replace("$TIME", str(delay)).split("\n"))
        self.queues[TAG_DISCORD].put(
            {
                "reply": f"[{self.server_config.display_name}]{_discord_message}",
                "args": {
                    "type": "chat",
                    "target": self.server_config.discord.chat_channel
                }
            }
        )

        # 存檔
        if self.server_config.clear_dino:
            with open("classlist", mode="r", encoding="utf-8") as class_file:
                class_list = class_file.read().split("\n")
            for class_name in class_list:
                self.add(f"DestroyWildDinoClasses \"{class_name}\" 1", TAG_SYSTEM, reply=False)
            self.add(f"DestroyWildDinos", TAG_SYSTEM, reply=False)
        self.add("save", TAG_SYSTEM, {"type": "id_tag", "content": "Finish"})

        if backup:
            source_dir = join(self.server_config.dir_path, "ShooterGame\\SavedArks\\Saved")
            backup_dir = join(self.server_config.dir_path, "ShooterGame\\SavedArks\\Backup", My_Datetime.fileformat())
            backup_root_dir = join(self.server_config.dir_path, "ShooterGame\\SavedArks\\Backup")
            if not isdir(backup_dir):
                makedirs(backup_dir)
            source_file = join(source_dir, self.server_config.file_name)
            backup_file = join(backup_dir, self.server_config.file_name)
            copyfile(source_file, backup_file)
            for filename in listdir(source_dir):
                if filename.endswith((".arkprofile", "arktribe", "arktributetribe")):
                    source_file = join(source_dir, filename)
                    backup_file = join(backup_dir, filename)
                    copyfile(source_file, backup_file)
                elif filename == "ServerPaintingsCache":
                    source_file = join(source_dir, filename)
                    backup_file = join(backup_dir, filename)
                    copytree(source_file, backup_file, dirs_exist_ok=True)
            timeout_date = (My_Datetime.now() - Config.time_setting.backup_day).isoformat().split("T")[0]
            for dir_name in listdir(backup_root_dir):
                if timeout_date in dir_name:
                    rmtree(join(backup_root_dir, dir_name), True, None)

        # 停止
        if mode < MODE_STOP:
            return
        while True:
            save_finish = self.get(TAG_SYSTEM)
            if save_finish != None:
                if save_finish["args"].get("type") == "id_tag" and save_finish["args"].get("content") == "Finish":
                    break
            sleep(_WHILE_SLEEP)
        self.add("DoExit")

        # 重啟
        if mode < MODE_RESTART:
            return
        while self.server_alive:
            sleep(_WHILE_SLEEP)
        self.start(tag)
    
    def _session(
        self,
    ):
        config = self.server_config.rcon
        while True:
            try:
                if not self.server_alive:
                    self.in_queue.clear()
                with Client(
                    host=config.address,
                    port=config.port,
                    timeout=config.timeout,
                    passwd=config.password
                ) as client:
                    self.rcon_alive = True
                    self.server_alive = True
                    self.server_first_connect = False
                    logger.warning("RCON Connected!")
                    while True:
                        if not self.in_queue.empty():
                            requests = self.in_queue.get()
                            tag = requests["tag"]
                            need_reply = requests["need_reply"]
                            command = requests["command"]
                            logger.info(f"From:{_TAG_LIST[tag]} Receive Command:{command} Args:{requests.get('args', 'No Args')}")
                            reply = client.run(command)
                            requests["reply"] = reply
                            del requests["tag"]
                            del requests["need_reply"]
                            if need_reply:
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
                                self.queues[TAG_DISCORD].put(
                                    {
                                        "reply": f"[{self.server_config.display_name}]{message}",
                                        "args": {
                                            "type": "chat",
                                            "target": self.server_config.discord.chat_channel
                                        }
                                    }
                                )
                        sleep(_WHILE_SLEEP)
            except SystemExit:
                raise SystemExit
            except Exception as e:
                logger.debug(f"RCON Exception: {e}")
                try:
                    # 閃斷測試
                    for _ in range(5):
                        sleep(1)
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
                            if _ark_is_alive(self.server_config.dir_path) and not self.server_alive:
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
                            if not _ark_is_alive(self.server_config.dir_path) and self.server_alive:
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