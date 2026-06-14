"""Application metrics collection."""
import time
from typing import Dict, Any
from collections import defaultdict

class Metrics:
    def __init__(self):
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, list] = defaultdict(list)
        self.timings: Dict[str, list] = defaultdict(list)
    
    def increment(self, name: str, value: int = 1):
        self.counters[name] += value
    
    def gauge(self, name: str, value: float):
        self.gauges[name] = value
    
    def record(self, name: str, value: float):
        self.histograms[name].append(value)
    
    def time(self, name: str):
        start = time.time()
        return lambda: self.timings[name].append(time.time() - start)
    
    def summary(self) -> Dict[str, Any]:
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {k: {"count": len(v), "avg": sum(v)/len(v)} for k, v in self.histograms.items()},
        }
