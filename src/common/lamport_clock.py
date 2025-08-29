import threading

class LamportClock:
    def __init__(self):
        self.time = 0
        self._lock = threading.Lock()

    def increment(self):
        with self._lock:
            self.time += 1
            return self.time

    def update(self, received_time):
        with self._lock:
            self.time = max(self.time, received_time) + 1
            return self.time

    def get_time(self):
        with self._lock:
            return self.time
