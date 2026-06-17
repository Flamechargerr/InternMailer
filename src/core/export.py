"""Export utilities for application data."""
import csv
import json
from typing import List, Dict
from pathlib import Path

class Exporter:
    @staticmethod
    def to_csv(data: List[Dict], path: str):
        if not data:
            return
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    
    @staticmethod
    def to_json(data: List[Dict], path: str):
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    
    @staticmethod
    def to_markdown(data: List[Dict], path: str, title: str = "Report"):
        lines = [f"# {title}\n", "| " + " | ".join(data[0].keys()) + " |", 
                 "|" + "|".join("---" for _ in data[0].keys()) + "|"]
        for row in data:
            lines.append("| " + " | ".join(str(v) for v in row.values()) + " |")
        Path(path).write_text("\n".join(lines))
