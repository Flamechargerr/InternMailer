"""
Enhanced Configuration Manager with Conflict Resolution
======================================================

This module provides a unified configuration manager that:
1. Resolves conflicts between duplicate configuration variables
2. Provides comprehensive validation with actionable error messages
3. Logs configuration state for debugging
4. Handles missing configuration files with sensible defaults
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import yaml
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class ValidationIssue:
    """Represents a configuration validation issue"""
    severity: str  # "error", "warning", "info"
    message: str
    variable: Optional[str] = None
    suggestion: Optional[str] = None

@dataclass
class EmailCredentials:
    """Unified email credentials with conflict resolution"""
    user: str
    password: str
    source: str  # Which variable was used: "gmail", "sender", "email"
    resolved_conflicts: List[str] = field(default_factory=list)

@dataclass
class SystemConfiguration:
    """Unified system configuration with resolved conflicts"""
    # Email Configuration (resolved)
    email_credentials: EmailCredentials
    
    # Resume Path (resolved)
    resume_path: Optional[Path]
    resume_path_source: str  # Which variable was used
    
    # AI Configuration
    groq_api_key: str
    groq_model: str
    openrouter_api_key: str
    github_token: str
    openai_api_key: str
    hunter_api_key: str
    apollo_api_key: str
    
    # Job Discovery
    job_sources_path: Path
    job_score_threshold: float
    job_target_locations: List[str]
    job_role_keywords: List[str]
    job_season_start: str
    job_season_end: str
    
    # Email Settings
    max_emails_per_day: int
    max_concurrent_emails: int
    rate_limit_delay: float
    
    # Feature Flags
    email_skip_academic: bool
    contact_discovery_enabled: bool
    contact_discovery_daily_cap: int
    email_strict_template: bool
    
    # Validation issues
    validation_issues: List[ValidationIssue] = field(default_factory=list)
    
    def is_valid(self) -> bool:
        """Check if configuration is valid (no errors)"""
        return not any(issue.severity == "error" for issue in self.validation_issues)
    
    def has_warnings(self) -> bool:
        """Check if configuration has warnings"""
        return any(issue.severity == "warning" for issue in self.validation_issues)


class ConfigurationManager:
    """
    Enhanced configuration manager with conflict resolution and validation
    """
    
    def __init__(self, env_file: str = ".env"):
        """Initialize configuration manager"""
        # Try TCC-safe shadow first, then project root
        shadow_env = Path('/tmp/internmailer_db/.env')
        if shadow_env.exists():
            self.env_file = str(shadow_env)
        else:
            # Resolve to the actual project root (internmailer-repo/)
            project_root = Path(__file__).resolve().parent.parent.parent
            self.env_file = str(project_root / env_file)
        self.config: Optional[SystemConfiguration] = None
        self.raw_env_vars: Dict[str, str] = {}
        self.loaded_files: List[str] = []
        
    def load(self) -> SystemConfiguration:
        """Load and validate configuration"""
        logger.info("Loading configuration...")
        
        # Load environment variables
        self._load_environment_variables()
        
        # Resolve conflicts and create unified configuration
        self.config = self._resolve_configuration()
        
        # Validate configuration
        self._validate_configuration()
        
        # Log configuration state
        self._log_configuration_state()
        
        return self.config
    
    def _load_environment_variables(self) -> None:
        """Load environment variables from .env file"""
        env_found = False

        # os.path.exists() may return False under macOS TCC even when the file
        # is readable.  Fall back to trying to open the file directly.
        if os.path.exists(self.env_file):
            env_found = True
        else:
            try:
                with open(self.env_file, "r"):
                    pass
                env_found = True
            except (PermissionError, OSError):
                pass

        if env_found:
            logger.info(f"Loading environment variables from {self.env_file}")
            load_dotenv(self.env_file)
            self.loaded_files.append(self.env_file)
        else:
            logger.warning(f"Environment file {self.env_file} not found, using system environment")
        
        # Collect all relevant environment variables
        self.raw_env_vars = {
            # Email credentials (potential conflicts)
            "GMAIL_USER": os.getenv("GMAIL_USER", ""),
            "GMAIL_APP_PASSWORD": os.getenv("GMAIL_APP_PASSWORD", ""),
            "SENDER_EMAIL": os.getenv("SENDER_EMAIL", ""),
            "SENDER_PASSWORD": os.getenv("SENDER_PASSWORD", ""),
            "EMAIL_ADDRESS": os.getenv("EMAIL_ADDRESS", ""),
            "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD", ""),
            
            # Resume paths (potential conflicts)
            "RESUME_PATHS": os.getenv("RESUME_PATHS", ""),
            "RESUME_PATH": os.getenv("RESUME_PATH", ""),
            "RESUME_PDF_PATH": os.getenv("RESUME_PDF_PATH", ""),
            
            # AI Configuration
            "GROQ_API_KEY": os.getenv("GROQ_API_KEY", ""),
            "GROQ_MODEL": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY", ""),
            "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN", ""),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
            "HUNTER_API_KEY": os.getenv("HUNTER_API_KEY", ""),
            "APOLLO_API_KEY": os.getenv("APOLLO_API_KEY", ""),
            
            # Job Discovery
            "JOB_SOURCES_PATH": os.getenv("JOB_SOURCES_PATH", "data/job_sources.yaml"),
            "JOB_SCORE_THRESHOLD": os.getenv("JOB_SCORE_THRESHOLD", "0.6"),
            "JOB_TARGET_LOCATIONS": os.getenv("JOB_TARGET_LOCATIONS", "India"),
            "JOB_ROLE_KEYWORDS": os.getenv("JOB_ROLE_KEYWORDS", "intern,internship,sde,software engineer,analyst,tech"),
            "JOB_SEASON_START": os.getenv("JOB_SEASON_START", "2026-05-01"),
            "JOB_SEASON_END": os.getenv("JOB_SEASON_END", "2026-07-31"),
            
            # Email Settings
            "MAX_EMAILS_PER_DAY": os.getenv("MAX_EMAILS_PER_DAY", "100"),
            "MAX_CONCURRENT_EMAILS": os.getenv("MAX_CONCURRENT_EMAILS", "12"),
            "RATE_LIMIT_DELAY": os.getenv("RATE_LIMIT_DELAY", "0.1"),
            
            # Feature Flags
            "EMAIL_SKIP_ACADEMIC": os.getenv("EMAIL_SKIP_ACADEMIC", "true"),
            "CONTACT_DISCOVERY_ENABLED": os.getenv("CONTACT_DISCOVERY_ENABLED", "true"),
            "CONTACT_DISCOVERY_DAILY_CAP": os.getenv("CONTACT_DISCOVERY_DAILY_CAP", "100"),
            "EMAIL_STRICT_TEMPLATE": os.getenv("EMAIL_STRICT_TEMPLATE", "true"),
        }
        
        # Log loaded variables (without sensitive data)
        safe_vars = {k: "[REDACTED]" if "PASSWORD" in k or "KEY" in k else v 
                    for k, v in self.raw_env_vars.items()}
        logger.debug(f"Loaded environment variables: {safe_vars}")
    
    def _resolve_email_credentials(self) -> Tuple[EmailCredentials, List[ValidationIssue]]:
        """Resolve email credential conflicts"""
        issues = []
        resolved_conflicts = []
        
        # Collect all email credential options
        email_options = [
            ("GMAIL_USER", "GMAIL_APP_PASSWORD", "gmail"),
            ("SENDER_EMAIL", "SENDER_PASSWORD", "sender"),
            ("EMAIL_ADDRESS", "EMAIL_PASSWORD", "email"),
        ]
        
        # Find the first complete pair
        selected_user = ""
        selected_password = ""
        selected_source = ""
        
        for user_var, password_var, source in email_options:
            user = self.raw_env_vars.get(user_var, "")
            password = self.raw_env_vars.get(password_var, "")
            
            if user and password:
                selected_user = user
                selected_password = password
                selected_source = source
                
                # Check for conflicts with other options
                for other_user_var, other_password_var, other_source in email_options:
                    if other_source != source:
                        other_user = self.raw_env_vars.get(other_user_var, "")
                        other_password = self.raw_env_vars.get(other_password_var, "")
                        
                        if other_user and other_user != user:
                            resolved_conflicts.append(f"{other_user_var} conflicts with {user_var}, using {user_var}")
                        
                        if other_password and other_password != password:
                            resolved_conflicts.append(f"{other_password_var} conflicts with {password_var}, using {password_var}")
                
                break
        
        # If no complete pair found, check for partial configurations
        if not selected_user or not selected_password:
            # Try to assemble from different sources
            user_candidates = [
                self.raw_env_vars.get("GMAIL_USER", ""),
                self.raw_env_vars.get("SENDER_EMAIL", ""),
                self.raw_env_vars.get("EMAIL_ADDRESS", ""),
            ]
            
            password_candidates = [
                self.raw_env_vars.get("GMAIL_APP_PASSWORD", ""),
                self.raw_env_vars.get("SENDER_PASSWORD", ""),
                self.raw_env_vars.get("EMAIL_PASSWORD", ""),
            ]
            
            selected_user = next((u for u in user_candidates if u), "")
            selected_password = next((p for p in password_candidates if p), "")
            selected_source = "mixed"
            
            if selected_user and selected_password:
                issues.append(ValidationIssue(
                    severity="warning",
                    message="Email credentials assembled from multiple sources",
                    variable="EMAIL_CREDENTIALS",
                    suggestion="Use consistent GMAIL_USER/GMAIL_APP_PASSWORD or SENDER_EMAIL/SENDER_PASSWORD pairs"
                ))
        
        # Validate the selected credentials
        if not selected_user:
            issues.append(ValidationIssue(
                severity="error",
                message="No email user configured",
                variable="GMAIL_USER/SENDER_EMAIL/EMAIL_ADDRESS",
                suggestion="Set GMAIL_USER, SENDER_EMAIL, or EMAIL_ADDRESS in .env file"
            ))
        
        if not selected_password:
            issues.append(ValidationIssue(
                severity="error",
                message="No email password configured",
                variable="GMAIL_APP_PASSWORD/SENDER_PASSWORD/EMAIL_PASSWORD",
                suggestion="Set GMAIL_APP_PASSWORD, SENDER_PASSWORD, or EMAIL_PASSWORD in .env file"
            ))
        
        if selected_user and "@" not in selected_user:
            issues.append(ValidationIssue(
                severity="warning",
                message="Email user doesn't look like a valid email address",
                variable=selected_source.upper() + "_USER",
                suggestion="Ensure email address is in format 'user@example.com'"
            ))
        
        return EmailCredentials(
            user=selected_user,
            password=selected_password,
            source=selected_source,
            resolved_conflicts=resolved_conflicts
        ), issues
    
    def _resolve_resume_path(self) -> Tuple[Optional[Path], str, List[ValidationIssue]]:
        """Resolve resume path conflicts"""
        issues = []
        resolved_conflicts = []
        
        # Collect all resume path options
        path_options = [
            ("RESUME_PATHS", "RESUME_PATHS"),
            ("RESUME_PATH", "RESUME_PATH"),
            ("RESUME_PDF_PATH", "RESUME_PDF_PATH"),
        ]
        
        # Find the first non-empty path
        selected_path = None
        selected_source = ""
        
        for var_name, source in path_options:
            path_str = self.raw_env_vars.get(var_name, "")
            if path_str:
                try:
                    path = Path(path_str)
                    try:
                        path_exists = path.exists()
                    except PermissionError:
                        path_exists = False
                    if path_exists:
                        selected_path = path
                        selected_source = source
                        
                        # Check for conflicts with other options
                        for other_var_name, other_source in path_options:
                            if other_source != source:
                                other_path_str = self.raw_env_vars.get(other_var_name, "")
                                if other_path_str and other_path_str != path_str:
                                    resolved_conflicts.append(f"{other_var_name} conflicts with {var_name}, using {var_name}")
                        
                        break
                    else:
                        issues.append(ValidationIssue(
                            severity="warning",
                            message=f"Resume path does not exist: {path_str}",
                            variable=var_name,
                            suggestion="Check the file path or update the variable"
                        ))
                except Exception as e:
                    issues.append(ValidationIssue(
                        severity="warning",
                        message=f"Invalid resume path format: {path_str}",
                        variable=var_name,
                        suggestion=f"Error: {str(e)}"
                    ))
        
        if not selected_path:
            issues.append(ValidationIssue(
                severity="warning",
                message="No resume path configured",
                variable="RESUME_PATHS/RESUME_PATH/RESUME_PDF_PATH",
                suggestion="Set RESUME_PATH to your resume PDF file path"
            ))
        
        return selected_path, selected_source, issues
    
    def _resolve_configuration(self) -> SystemConfiguration:
        """Resolve all configuration conflicts and create unified configuration"""
        logger.info("Resolving configuration conflicts...")
        
        # Resolve email credentials
        email_credentials, email_issues = self._resolve_email_credentials()
        
        # Resolve resume path
        resume_path, resume_source, resume_issues = self._resolve_resume_path()
        
        # Parse list-based configurations
        target_locations = [loc.strip() for loc in self.raw_env_vars["JOB_TARGET_LOCATIONS"].split(",") if loc.strip()]
        role_keywords = [kw.strip() for kw in self.raw_env_vars["JOB_ROLE_KEYWORDS"].split(",") if kw.strip()]
        
        # Create unified configuration
        config = SystemConfiguration(
            email_credentials=email_credentials,
            resume_path=resume_path,
            resume_path_source=resume_source,
            groq_api_key=self.raw_env_vars["GROQ_API_KEY"],
            groq_model=self.raw_env_vars["GROQ_MODEL"],
            openrouter_api_key=self.raw_env_vars["OPENROUTER_API_KEY"],
            github_token=self.raw_env_vars["GITHUB_TOKEN"],
            openai_api_key=self.raw_env_vars["OPENAI_API_KEY"],
            hunter_api_key=self.raw_env_vars["HUNTER_API_KEY"],
            apollo_api_key=self.raw_env_vars["APOLLO_API_KEY"],
            job_sources_path=Path(self.raw_env_vars["JOB_SOURCES_PATH"]),
            job_score_threshold=float(self.raw_env_vars["JOB_SCORE_THRESHOLD"]),
            job_target_locations=target_locations,
            job_role_keywords=role_keywords,
            job_season_start=self.raw_env_vars["JOB_SEASON_START"],
            job_season_end=self.raw_env_vars["JOB_SEASON_END"],
            max_emails_per_day=int(self.raw_env_vars["MAX_EMAILS_PER_DAY"]),
            max_concurrent_emails=int(self.raw_env_vars["MAX_CONCURRENT_EMAILS"]),
            rate_limit_delay=float(self.raw_env_vars["RATE_LIMIT_DELAY"]),
            email_skip_academic=self.raw_env_vars["EMAIL_SKIP_ACADEMIC"].lower() == "true",
            contact_discovery_enabled=self.raw_env_vars["CONTACT_DISCOVERY_ENABLED"].lower() == "true",
            contact_discovery_daily_cap=int(self.raw_env_vars["CONTACT_DISCOVERY_DAILY_CAP"]),
            email_strict_template=self.raw_env_vars["EMAIL_STRICT_TEMPLATE"].lower() == "true",
            validation_issues=email_issues + resume_issues
        )
        
        return config
    
    def _validate_configuration(self) -> None:
        """Perform comprehensive configuration validation"""
        logger.info("Validating configuration...")
        
        if not self.config:
            return
        
        issues = self.config.validation_issues
        
        # Validate email credentials format
        if self.config.email_credentials.user:
            if "@" not in self.config.email_credentials.user:
                issues.append(ValidationIssue(
                    severity="error",
                    message="Email user is not a valid email address",
                    variable=f"{self.config.email_credentials.source.upper()}_USER",
                    suggestion="Email should be in format 'user@example.com'"
                ))
        
        # Validate numeric values
        if self.config.max_emails_per_day <= 0:
            issues.append(ValidationIssue(
                severity="error",
                message="MAX_EMAILS_PER_DAY must be positive",
                variable="MAX_EMAILS_PER_DAY",
                suggestion="Set to a positive integer (e.g., 100)"
            ))
        
        if self.config.max_concurrent_emails <= 0:
            issues.append(ValidationIssue(
                severity="error",
                message="MAX_CONCURRENT_EMAILS must be positive",
                variable="MAX_CONCURRENT_EMAILS",
                suggestion="Set to a positive integer (e.g., 10)"
            ))
        
        if self.config.rate_limit_delay < 0:
            issues.append(ValidationIssue(
                severity="error",
                message="RATE_LIMIT_DELAY cannot be negative",
                variable="RATE_LIMIT_DELAY",
                suggestion="Set to a positive float (e.g., 0.1)"
            ))
        
        # Validate job score threshold
        if not 0 <= self.config.job_score_threshold <= 1:
            issues.append(ValidationIssue(
                severity="error",
                message="JOB_SCORE_THRESHOLD must be between 0 and 1",
                variable="JOB_SCORE_THRESHOLD",
                suggestion="Set to a value between 0.0 and 1.0 (e.g., 0.6)"
            ))
        
        # Validate job sources file exists
        try:
            job_sources_exists = self.config.job_sources_path.exists()
        except PermissionError:
            job_sources_exists = False
        if not job_sources_exists:
            issues.append(ValidationIssue(
                severity="warning",
                message=f"Job sources file not found: {self.config.job_sources_path}",
                variable="JOB_SOURCES_PATH",
                suggestion="Create the file or update the path"
            ))
        
        # Validate resume path if configured
        try:
            resume_exists = self.config.resume_path.exists() if self.config.resume_path else True
        except PermissionError:
            resume_exists = False
        if self.config.resume_path and not resume_exists:
            issues.append(ValidationIssue(
                severity="warning",
                message=f"Resume file not found: {self.config.resume_path}",
                variable=self.config.resume_path_source,
                suggestion="Check the file path or update the variable"
            ))
        
        # Update validation issues
        self.config.validation_issues = issues
    
    def _log_configuration_state(self) -> None:
        """Log configuration state for debugging"""
        if not self.config:
            return
        
        logger.info("Configuration loaded successfully")
        
        # Log resolved conflicts
        if self.config.email_credentials.resolved_conflicts:
            logger.info(f"Resolved email credential conflicts: {self.config.email_credentials.resolved_conflicts}")
        
        # Log validation issues
        if self.config.validation_issues:
            error_count = sum(1 for issue in self.config.validation_issues if issue.severity == "error")
            warning_count = sum(1 for issue in self.config.validation_issues if issue.severity == "warning")
            
            logger.info(f"Configuration validation: {error_count} errors, {warning_count} warnings")
            
            for issue in self.config.validation_issues:
                log_level = logging.ERROR if issue.severity == "error" else logging.WARNING
                logger.log(log_level, f"{issue.severity.upper()}: {issue.message}")
                if issue.suggestion:
                    logger.log(log_level, f"  Suggestion: {issue.suggestion}")
        
        # Log configuration summary (without sensitive data)
        safe_config = {
            "email_user": self.config.email_credentials.user,
            "email_source": self.config.email_credentials.source,
            "resume_path": str(self.config.resume_path) if self.config.resume_path else None,
            "resume_source": self.config.resume_path_source,
            "job_sources_path": str(self.config.job_sources_path),
            "job_score_threshold": self.config.job_score_threshold,
            "max_emails_per_day": self.config.max_emails_per_day,
            "max_concurrent_emails": self.config.max_concurrent_emails,
            "is_valid": self.config.is_valid(),
            "has_warnings": self.config.has_warnings(),
        }
        
        logger.debug(f"Configuration summary: {safe_config}")
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get configuration summary for display"""
        if not self.config:
            return {"error": "Configuration not loaded"}
        
        return {
            "loaded_files": self.loaded_files,
            "email": {
                "user": self.config.email_credentials.user,
                "source": self.config.email_credentials.source,
                "resolved_conflicts": self.config.email_credentials.resolved_conflicts,
            },
            "resume": {
                "path": str(self.config.resume_path) if self.config.resume_path else None,
                "source": self.config.resume_path_source,
            },
            "job_discovery": {
                "sources_path": str(self.config.job_sources_path),
                "score_threshold": self.config.job_score_threshold,
                "target_locations": self.config.job_target_locations,
                "role_keywords": self.config.job_role_keywords,
                "season_start": self.config.job_season_start,
                "season_end": self.config.job_season_end,
            },
            "email_settings": {
                "max_per_day": self.config.max_emails_per_day,
                "max_concurrent": self.config.max_concurrent_emails,
                "rate_limit_delay": self.config.rate_limit_delay,
            },
            "feature_flags": {
                "email_skip_academic": self.config.email_skip_academic,
                "contact_discovery_enabled": self.config.contact_discovery_enabled,
                "contact_discovery_daily_cap": self.config.contact_discovery_daily_cap,
                "email_strict_template": self.config.email_strict_template,
            },
            "validation": {
                "is_valid": self.config.is_valid(),
                "has_warnings": self.config.has_warnings(),
                "issues": [
                    {
                        "severity": issue.severity,
                        "message": issue.message,
                        "variable": issue.variable,
                        "suggestion": issue.suggestion,
                    }
                    for issue in self.config.validation_issues
                ],
            },
        }


# Singleton instance
_config_manager: Optional[ConfigurationManager] = None

def get_configuration_manager() -> ConfigurationManager:
    """Get singleton configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
        _config_manager.load()
    return _config_manager

def get_config() -> SystemConfiguration:
    """Get the loaded configuration"""
    manager = get_configuration_manager()
    return manager.config