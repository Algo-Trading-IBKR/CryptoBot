from threading import Thread
from queue import Queue

class OrderManager(Thread):
    def __init__(self, bot):
        Thread.__init__(self, daemon=True)

        self.queue = Queue(-1)

    def run(self):
        while True:
            coin = self.queue.get()

            # do some shit

            self.queue.task_done()
