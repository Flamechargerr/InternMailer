"""Email template engine with variable substitution."""
import re
from typing import Dict

class EmailTemplate:
    def __init__(self, template: str):
        self.template = template
        self.variables = re.findall(r"\{\{(\w+)\}\}", template)
    
    def render(self, context: Dict) -> str:
        result = self.template
        for key, val in context.items():
            result = result.replace(f"{{{{{key}}}}}", str(val))
        return result
    
    def validate(self, context: Dict) -> bool:
        return all(v in context for v in self.variables)
