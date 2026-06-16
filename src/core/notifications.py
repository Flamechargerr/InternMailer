"""Desktop notification support."""
import os
import subprocess
from typing import Optional

class Notifier:
    @staticmethod
    def notify(title: str, message: str, sound: bool = False):
        system = os.uname().sysname if hasattr(os, "uname") else "Unknown"
        if system == "Darwin":
            subprocess.run(["osascript", "-e", f'display notification "{message}" with title "{title}"'])
        elif system == "Linux":
            subprocess.run(["notify-send", title, message])
    
    @staticmethod
    def alert_job_applied(company: str, position: str):
        Notifier.notify("Job Applied", f"Successfully applied to {position} at {company}")
    
    @staticmethod
    def alert_reply_received(sender: str, subject: str):
        Notifier.notify("Reply Received", f"From {sender}: {subject}")
