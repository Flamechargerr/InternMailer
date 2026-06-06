"""Task scheduler with cron-like expressions."""
import threading
import time
from datetime import datetime, timedelta
from typing import Callable, List

class TaskScheduler:
    def __init__(self):
        self.tasks: List[dict] = []
        self._running = False
        self._thread: threading.Thread = None
    
    def add(self, name: str, interval: int, fn: Callable, args=()):
        self.tasks.append({
            "name": name,
            "interval": interval,
            "fn": fn,
            "args": args,
            "last_run": datetime.min,
        })
    
    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
    
    def _loop(self):
        while self._running:
            now = datetime.now()
            for task in self.tasks:
                elapsed = (now - task["last_run"]).total_seconds()
                if elapsed >= task["interval"]:
                    try:
                        task["fn"](*task["args"])
                    except Exception as e:
                        print(f"Task {task['name']} failed: {e}")
                    task["last_run"] = now
            time.sleep(1)
