import logging
import fitz  # PyMuPDF
from typing import Dict, Any
import os

try:
    from .parsing.parser_interface import ResumeParserInterface, ParsingError, ResumeData
    from .parsing.azure_ai_parser import AzureAIResumeParser
    from .parsing.rule_based_parser import RuleBasedParser
except ImportError:
    # Fallback for direct execution or testing
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from parsing.parser_interface import ResumeParserInterface, ParsingError, ResumeData
    from parsing.azure_ai_parser import AzureAIResumeParser
    from parsing.rule_based_parser import RuleBasedParser

logging.basicConfig(level=logging.INFO)


class ResumeParser:
    """
    Orchestrator for resume parsing using different providers.
    Automatically switches between providers based on availability.
    """

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text = ""
        self.data = {}
        # Prioritize Azure AI but keep rule-based as fallback with explicit logging
        self.providers = [AzureAIResumeParser(), RuleBasedParser()]

    def extract_text(self) -> str:
        """Extracts text from a resume PDF file."""
        try:
            doc = fitz.open(self.pdf_path)
            self.text = "\n".join(page.get_text() for page in doc)
            logging.info(f"Text extracted from {self.pdf_path}")
            return self.text
        except Exception as e:
            logging.error(f"Error extracting text: {e}")
            raise ParsingError("Failed to extract text", original_error=e)

    def parse(self) -> Dict[str, Any]:
        """Parses the resume using available providers."""
        if not self.text:
            self.extract_text()

        last_exception = None
        for provider in self.providers:
            if provider.is_available():
                try:
                    logging.info(f"Attempting to parse with {provider.get_provider_name()}")
                    resume_data = provider.parse(self.text)
                    self.data = resume_data.to_dict()  # Store as dict for compatibility
                    logging.info(f"Parsing successful with {provider.get_provider_name()}")
                    return self.data
                except ParsingError as e:
                    logging.warning(f"Parsing failed with {provider.get_provider_name()}: {e}")
                    last_exception = e

        if not self.data and last_exception:
            raise last_exception
        elif not self.data:
            raise ParsingError("All parsing attempts failed.")

        return self.data

    def to_json(self, out_path: str = None) -> str:
        """Convert parsed data to JSON format."""
        if not self.data:
            self.parse()
        
        import json
        json_str = json.dumps(self.data, indent=2)
        if out_path:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(json_str)
            logging.info(f"Saved parsed data to {out_path}")
        return json_str
    
    # Compatibility methods for existing app code
    def parse_with_rules(self) -> Dict[str, Any]:
        """Compatibility method for rule-based parsing."""
        rule_parser = RuleBasedParser()
        if not self.text:
            self.extract_text()
        result = rule_parser.parse(self.text)
        return result.to_dict()
    
    def parse_with_llm(self) -> Dict[str, Any]:
        """Compatibility method for LLM parsing."""
        if not self.text:
            self.extract_text()
        
        # Try Azure AI first, then rule-based fallback
        for parser_class in [AzureAIResumeParser]:
            parser = parser_class()
            if parser.is_available():
                try:
                    result = parser.parse(self.text)
                    return result.to_dict()
                except ParsingError:
                    continue
        
        return {}
    
    def parse_with_template_fallback(self) -> Dict[str, Any]:
        """Lightweight template-based fallback parser (compatibility)."""
        return self.parse_with_rules()

    
