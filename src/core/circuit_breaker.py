"""Circuit breaker pattern for external services."""
import time
from enum import Enum

class State(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, threshold=5, timeout=60):
        self.threshold = threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure = None
        self.state = State.CLOSED
    
    def call(self, fn, *args, **kwargs):
        if self.state == State.OPEN:
            if time.time() - self.last_failure > self.timeout:
                self.state = State.HALF_OPEN
            else:
                raise Exception("Circuit breaker open")
        try:
            result = fn(*args, **kwargs)
            self.failures = 0
            self.state = State.CLOSED
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure = time.time()
            if self.failures >= self.threshold:
                self.state = State.OPEN
            raise e
