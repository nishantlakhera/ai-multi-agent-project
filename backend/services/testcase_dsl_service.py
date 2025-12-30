from typing import Dict, Any, Optional
import json
from config.langchain_config import get_langchain_llm
from utils.helpers import load_prompt
from utils.json_utils import safe_json_loads
from utils.logger import logger

llm = get_langchain_llm(temperature=0.2)

def generate_test_dsl(
    test_case: Dict[str, Any],
    base_url: Optional[str] = None,
    test_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    prompt = load_prompt("testcase_dsl").format(
        scenario=test_case.get("scenario", ""),
        steps="\n".join(test_case.get("steps", []) if isinstance(test_case.get("steps", []), list) else []),
        test_data="\n".join(test_case.get("test_data", []) if isinstance(test_case.get("test_data", []), list) else []),
        test_data_json=json.dumps(test_data or {}),
        expected="\n".join(test_case.get("expected", []) if isinstance(test_case.get("expected", []), list) else []),
        base_url=base_url or "",
    )
    response = llm.invoke(prompt)
    try:
        return safe_json_loads(response.content)
    except Exception as e:
        logger.error(f"[testcase_dsl] Failed to parse JSON: {e}", exc_info=True)
        logger.error(f"[testcase_dsl] Raw response (truncated): {response.content[:800]}")
        try:
            fix_prompt = load_prompt("json_fix").format(text=response.content)
            fixed = llm.invoke(fix_prompt)
            return safe_json_loads(fixed.content)
        except Exception as fix_error:
            logger.error(f"[testcase_dsl] Failed to fix JSON: {fix_error}", exc_info=True)
            return {"name": test_case.get("id", "unnamed"), "steps": []}
