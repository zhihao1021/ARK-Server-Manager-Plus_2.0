import queue

class Queue(queue.Queue):
    """
    可清除式佇列。
    新增:
     - clear(): 清除佇列。
    """
    def clear(self):
        while not self.empty():
            self.get()