"""
Application Tracker Module

This module tracks job applications, their statuses,
and manages the application workflow.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any


class ApplicationTracker:
    """Track job applications and their status throughout the process."""
    
    def __init__(self, log_file: str = "data/application_log.json"):
        """Initialize the application tracker with a log file."""
        self.log_file = log_file
        self.applications = self._load_log()
    
    def _load_log(self) -> List[Dict[str, Any]]:
        """Load existing application log from file."""
        if not os.path.exists(self.log_file):
            return []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_log(self):
        """Save application log to file."""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.applications, f, indent=2, default=str)
    
    def add_application(self, job_data: Dict[str, Any], status: str = "ready_to_apply") -> int:
        """
        Add a new job application to track.
        
        Args:
            job_data: Job information including title, company, etc.
            status: Initial status of the application
        
        Returns:
            Application ID (index in the list)
        """
        application = {
            "id": len(self.applications),
            "job_title": job_data.get("title", "Unknown"),
            "company": job_data.get("company", "Unknown"),
            "location": job_data.get("location", "Unknown"),
            "job_url": job_data.get("url", ""),
            "skills_required": job_data.get("skills", []),
            "status": status,
            "applied_date": None,
            "application_method": "",
            "notes": "",
            "follow_up_date": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.applications.append(application)
        self._save_log()
        return application["id"]
    
    def update_status(self, application_id: int, new_status: str, notes: str = ""):
        """
        Update the status of an application.
        
        Args:
            application_id: ID of the application to update
            new_status: New status value
            notes: Optional notes about the status change
        """
        if 0 <= application_id < len(self.applications):
            self.applications[application_id]["status"] = new_status
            self.applications[application_id]["updated_at"] = datetime.now().isoformat()
            
            # Set applied_date when status changes to "applied"
            if new_status == "applied" and not self.applications[application_id]["applied_date"]:
                self.applications[application_id]["applied_date"] = datetime.now().isoformat()
            
            # Add notes if provided
            if notes:
                existing_notes = self.applications[application_id].get("notes", "")
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                new_note = f"[{timestamp}] {notes}"
                self.applications[application_id]["notes"] = f"{existing_notes}\n{new_note}".strip()
            
            self._save_log()
        else:
            raise IndexError(f"Application ID {application_id} not found")
    
    def get_application(self, application_id: int) -> Dict[str, Any]:
        """Get a specific application by ID."""
        if 0 <= application_id < len(self.applications):
            return self.applications[application_id]
        else:
            raise IndexError(f"Application ID {application_id} not found")
    
    def get_applications_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all applications with a specific status."""
        return [app for app in self.applications if app["status"] == status]
    
    def get_applications_by_company(self, company: str) -> List[Dict[str, Any]]:
        """Get all applications for a specific company."""
        return [app for app in self.applications if app["company"].lower() == company.lower()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about applications."""
        if not self.applications:
            return {"total_applications": 0}
        
        status_counts = {}
        companies = set()
        
        for app in self.applications:
            status = app["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            companies.add(app["company"])
        
        return {
            "total_applications": len(self.applications),
            "unique_companies": len(companies),
            "status_breakdown": status_counts,
            "most_recent_application": max(self.applications, key=lambda x: x["created_at"])["job_title"] if self.applications else None
        }
    
    def export_applications(self, filename: str = None) -> str:
        """Export applications to a JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"applications_export_{timestamp}.json"
        
        export_path = os.path.join("data", filename)
        os.makedirs("data", exist_ok=True)
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(self.applications, f, indent=2, default=str)
        
        return export_path
    
    def search_applications(self, query: str) -> List[Dict[str, Any]]:
        """Search applications by job title, company, or skills."""
        query_lower = query.lower()
        results = []
        
        for app in self.applications:
            if (query_lower in app["job_title"].lower() or 
                query_lower in app["company"].lower() or
                any(query_lower in skill.lower() for skill in app.get("skills_required", []))):
                results.append(app)
        
        return results


def main():
    """Test the application tracker."""
    tracker = ApplicationTracker()
    
    # Add sample applications
    sample_jobs = [
        {
            "title": "Data Scientist",
            "company": "Tech Corp",
            "location": "San Francisco",
            "skills": ["Python", "Machine Learning", "SQL"]
        },
        {
            "title": "Software Engineer",
            "company": "StartupXYZ", 
            "location": "Remote",
            "skills": ["JavaScript", "React", "Node.js"]
        }
    ]
    
    for job in sample_jobs:
        app_id = tracker.add_application(job)
        print(f"Added application {app_id}: {job['title']} at {job['company']}")
    
    # Update status
    tracker.update_status(0, "applied", "Applied through company website")
    
    # Get statistics
    stats = tracker.get_statistics()
    print(f"\nStatistics: {stats}")
    
    # Search applications
    results = tracker.search_applications("python")
    print(f"\nApplications matching 'python': {len(results)}")


if __name__ == "__main__":
    main()
