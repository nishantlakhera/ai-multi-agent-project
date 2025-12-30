import json
import re

def extract_json_block(text: str) -> str:
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            if "{" in part and "}" in part:
                text = part
                break
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return text

def safe_json_loads(text: str) -> dict:
    raw = extract_json_block(text)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cleaned = raw
        cleaned = cleaned.replace("“", "\"").replace("”", "\"").replace("’", "'")
        cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)
        return json.loads(cleaned)
