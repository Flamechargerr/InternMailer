"""
Validate JSON output against predefined schema.
"""

import os
import json
from jsonschema import validate, ValidationError
import pytest

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schemas', 'resume_schema.json')
PARSER_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'output', 'parsed_resume_data.json')


def test_parsed_resume_json_schema():
    """
    Validates the JSON output of the resume parser against a predefined schema file.
    """
    with open(SCHEMA_PATH, 'r') as schema_file:
        schema = json.load(schema_file)

    with open(PARSER_OUTPUT_PATH, 'r') as output_file:
        parsed_data = json.load(output_file)

    try:
        validate(instance=parsed_data, schema=schema)
        print("JSON Schema validation: PASSED")
    except ValidationError as e:
        print("JSON Schema validation: FAILED")
        raise AssertionError("Parsed resume data did not match the schema") from e


if __name__ == "__main__":
    pytest.main([__file__])
