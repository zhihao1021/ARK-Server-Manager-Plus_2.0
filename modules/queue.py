import queue

class Queue(queue.Queue):
    def clear(self):
        while not self.empty():
            self.get()