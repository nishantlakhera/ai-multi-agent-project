from typing import List, Dict, Any, Optional
import re

def _tokenize(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", text.lower()))

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()

def _select_best_case(
    cases: List[Dict[str, Any]],
    query: str,
    required_tags: Optional[List[str]],
    required_terms: Optional[List[str]],
) -> Optional[Dict[str, Any]]:
    required_tags = [t.strip().lower() for t in (required_tags or []) if isinstance(t, str)]
    required_terms = [t.strip().lower() for t in (required_terms or []) if isinstance(t, str)]
    query_tokens = _tokenize(query)

    best = None
    best_score = -1

    for case in cases:
        tags = [t.strip().lower() for t in case.get("tags", []) if isinstance(t, str)]
        scenario = case.get("scenario", "")
        steps = " ".join(case.get("steps", []) if isinstance(case.get("steps", []), list) else [])
        case_text = _normalize(f"{scenario} {steps}")

        score = 0
        if required_tags:
            overlap = set(tags) & set(required_tags)
            score += 2 * len(overlap)

        if required_terms:
            if not all(term in case_text for term in required_terms):
                continue
            score += 3 * len(required_terms)

        score += len(_tokenize(scenario) & query_tokens)
        score += len(_tokenize(steps) & query_tokens) * 0.5

        if score > best_score:
            best = case
            best_score = score

    return best

def select_best_case(
    cases: List[Dict[str, Any]],
    query: str,
    required_tags: Optional[List[str]] = None,
    required_terms: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    if not cases:
        return None

    return _select_best_case(cases, query, required_tags, required_terms)
    
