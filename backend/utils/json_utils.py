import json
import re

def _strip_json_comments(text: str) -> str:
    result = []
    in_string = False
    escape = False
    i = 0
    while i < len(text):
        char = text[i]
        if in_string:
            result.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            i += 1
            continue
        if char == '"':
            in_string = True
            result.append(char)
            i += 1
            continue
        if char == "/" and i + 1 < len(text) and text[i + 1] == "/":
            i += 2
            while i < len(text) and text[i] not in "\n\r":
                i += 1
            continue
        if char == "/" and i + 1 < len(text) and text[i + 1] == "*":
            i += 2
            while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        result.append(char)
        i += 1
    return "".join(result)

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
        cleaned = _strip_json_comments(raw)
        cleaned = cleaned.replace("“", "\"").replace("”", "\"").replace("’", "'")
        cleaned = re.sub(r'(name|label|text|placeholder|css)=\\\\\"([^\\\\\"]+)\\\\\"', r"\\1='\\2'", cleaned)
        cleaned = re.sub(r'(name|label|text|placeholder|css)=\\\\\"([^\\\\\"]+)\\\\\"\"', r"\\1='\\2'", cleaned)
        cleaned = re.sub(r'(name|label|text|placeholder|css)=\"([^\"]+)\"', r"\\1='\\2'", cleaned)
        cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            decoder = json.JSONDecoder()
            obj, _ = decoder.raw_decode(cleaned)
            return obj
