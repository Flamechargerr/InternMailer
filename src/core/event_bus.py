"""In-memory event bus for module communication."""
from typing import Callable, Dict, List
from threading import Lock

class EventBus:
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._lock = Lock()
    
    def subscribe(self, event: str, handler: Callable):
        with self._lock:
            self._handlers.setdefault(event, []).append(handler)
    
    def emit(self, event: str, *args, **kwargs):
        with self._lock:
            handlers = self._handlers.get(event, []).copy()
        for handler in handlers:
            try:
                handler(*args, **kwargs)
            except Exception as e:
                print(f"Handler error for {event}: {e}")
    
    def unsubscribe(self, event: str, handler: Callable):
        with self._lock:
            if event in self._handlers:
                self._handlers[event] = [h for h in self._handlers[event] if h != handler]
