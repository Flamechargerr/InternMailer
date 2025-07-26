import os
import logging
import json
from typing import Dict, Any
import fitz  # PyMuPDF
import requests

logging.basicConfig(level=logging.INFO)

class ResumeParser:
    """
    Parses a resume PDF to extract skills, domains, courses, and experience using Ollama LLM.
    """
    def __init__(self, pdf_path: str, ollama_url: str = "http://localhost:11434/api/generate", ollama_model: str = "gemma3"):
        self.pdf_path = pdf_path
        self.text = ""
        self.data = {}
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model

    def extract_text(self) -> str:
        try:
            doc = fitz.open(self.pdf_path)
            self.text = "\n".join(page.get_text() for page in doc)
            logging.info(f"Extracted text from {self.pdf_path}")
            return self.text
        except Exception as e:
            logging.error(f"Failed to extract text: {e}")
            return ""

    def parse_with_llm(self) -> Dict[str, Any]:
        if not self.text:
            self.extract_text()
        prompt = f"""
You are an expert resume parser. Extract the following from the resume text below and return as JSON:
- skills: list of technical and soft skills
- projects: list of project titles
- courses: list of relevant courses
- summary: a 2-3 sentence summary of the candidate

Resume text:
{self.text}

Return only valid JSON with keys: skills, projects, courses, summary.
"""
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False
        }
        try:
            response = requests.post(self.ollama_url, json=payload, timeout=90)
            response.raise_for_status()
            result = response.json().get("response", "")
            # Find the first valid JSON object in the response
            json_start = result.find('{')
            json_end = result.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                parsed = json.loads(result[json_start:json_end])
                logging.info("Parsed resume data with LLM.")
                return parsed
            else:
                logging.warning("LLM did not return valid JSON. Falling back.")
                return {}
        except Exception as e:
            logging.error(f"LLM resume parsing failed: {e}")
            return {}

    def parse(self) -> Dict[str, Any]:
        # Try LLM parsing first
        llm_data = self.parse_with_llm()
        if llm_data and any(llm_data.get(k) for k in ["skills", "projects", "courses"]):
            self.data = llm_data
            return self.data
        # Fallback: return empty lists and summary
        if not self.text:
            self.extract_text()
        self.data = {
            "skills": [],
            "projects": [],
            "courses": [],
            "domains": [],
            "experience": [],
            "summary": self.text[:500] if self.text else ""
        }
        logging.info("Fallback: Parsed resume data with empty fields.")
        return self.data

    def to_json(self, out_path: str = None) -> str:
        if not self.data:
            self.parse()
        json_str = json.dumps(self.data, indent=2)
        if out_path:
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            logging.info(f"Saved parsed data to {out_path}")
        return json_str

# TODO: Add unit tests for ResumeParser 