from typing import List, Dict, Any, Optional
import re

def _tokenize(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", text.lower()))

def select_best_case(cases: List[Dict[str, Any]], query: str, required_tags: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    if not cases:
        return None

    required_tags = [t.lower() for t in (required_tags or [])]
    query_tokens = _tokenize(query)

    best = None
    best_score = -1

    for case in cases:
        tags = [t.lower() for t in case.get("tags", []) if isinstance(t, str)]
        scenario = case.get("scenario", "")
        steps = " ".join(case.get("steps", []) if isinstance(case.get("steps", []), list) else [])

        score = 0
        if required_tags:
            if not all(t in tags for t in required_tags):
                continue
            score += 5 * len(required_tags)

        score += len(_tokenize(scenario) & query_tokens)
        score += len(_tokenize(steps) & query_tokens) * 0.5

        if score > best_score:
            best = case
            best_score = score

    return best
    