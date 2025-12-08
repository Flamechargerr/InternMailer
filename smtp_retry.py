"""
InternMailer - SMTP Retry Logic
Decorator-based retry with exponential backoff
"""

import time
import smtplib
from functools import wraps

def smtp_retry(max_retries=3, backoff_base=2):
    """
    Decorator to add SMTP retry logic with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_base: Base for exponential backoff (2 = 1s, 2s, 4s, 8s...)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    # Try to execute the function
                    result = func(*args, **kwargs)
                    
                    # If successful and it was a retry, log it
                    if attempt > 0:
                        print(f"   ✔️ Retry successful on attempt {attempt + 1}/{max_retries}")
                    
                    return result
                    
                except smtplib.SMTPServerDisconnected as e:
                    last_error = e
                    
                    if attempt < max_retries - 1:
                        wait_time = backoff_base ** attempt
                        print(f"   ⚠️ SMTP disconnected. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                    else:
                        print(f"   ❌ All {max_retries} retry attempts failed: {str(e)}")
                        raise
                
                except smtplib.SMTPException as e:
                    last_error = e
                    
                    if attempt < max_retries - 1:
                        wait_time = backoff_base ** attempt
                        print(f"   ⚠️ SMTP error: {str(e)}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        print(f"   ❌ All {max_retries} retry attempts failed: {str(e)}")
                        raise
                
                except Exception as e:
                    # Non-SMTP errors don't get retried
                    print(f"   ❌ Non-retryable error: {str(e)}")
                    raise
            
            # Should never reach here, but just in case
            if last_error:
                raise last_error
                
        return wrapper
    return decorator

# Example usage:
# @smtp_retry(max_retries=3)
# def send_email_function(...):
#     smtp.send_message(msg)
