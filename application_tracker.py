
import json
import datetime
from typing import Dict, List

class ApplicationTracker:
    def __init__(self, log_file: str = "data/application_log.json"):
        self.log_file = log_file
        self.applications = self._load_log()

    def _load_log(self) -> List[Dict]:
        try:
            with open(self.log_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_log(self):
        with open(self.log_file, 'w') as f:
            json.dump(self.applications, f, indent=4)

    def log_application(self, job_posting: Dict, status: str = "pending"):
        """
        Logs a new job application.
        """
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "job_title": job_posting.get('title'),
            "company": job_posting.get('company'),
            "status": status,  # e.g., pending, applied, rejected, interview
            "application_details": job_posting
        }
        self.applications.append(log_entry)
        self._save_log()
        print(f"Logged application for {job_posting.get('title')} at {job_posting.get('company')}")

    def update_status(self, application_id: int, new_status: str):
        """
        Updates the status of an existing application.
        """
        if 0 <= application_id < len(self.applications):
            self.applications[application_id]["status"] = new_status
            self.applications[application_id]["updated_at"] = datetime.datetime.now().isoformat()
            self._save_log()
            print(f"Updated application {application_id} to {new_status}")
        else:
            print(f"Error: Application ID {application_id} not found.")

    def get_applications_by_status(self, status: str) -> List[Dict]:
        """
        Retrieves all applications with a specific status.
        """
        return [app for app in self.applications if app["status"] == status]

    def display_summary(self):
        """
        Displays a summary of all logged applications.
        """
        if not self.applications:
            print("No applications logged yet.")
            return
        
        status_counts = {}
        for app in self.applications:
            status = app.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("--- Application Summary ---")
        for status, count in status_counts.items():
            print(f"- {status.capitalize()}: {count}")
        print("-------------------------")

if __name__ == "__main__":
    tracker = ApplicationTracker()
    
    # Example Usage:
    # 1. Load parsed jobs
    try:
        with open("data/parsed_jobs.json", 'r') as f:
            parsed_jobs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        parsed_jobs = []

    # 2. Log applications for the first two jobs
    if parsed_jobs:
        for job in parsed_jobs[:2]:
            tracker.log_application(job, status="applied")
        
        # 3. Display summary
        tracker.display_summary()
        
        # 4. Update status of the first application
        if tracker.applications:
            tracker.update_status(0, "interview")
            tracker.display_summary()
    else:
        print("No parsed jobs found. Run job_parser.py first.")


