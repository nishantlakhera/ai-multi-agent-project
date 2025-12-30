from typing import List, Dict, Any
from config.langchain_config import get_langchain_llm
from utils.helpers import load_prompt
from utils.json_utils import safe_json_loads
from utils.logger import logger

llm = get_langchain_llm(temperature=0.2)

def extract_test_cases(context: str) -> List[Dict[str, Any]]:
    prompt = load_prompt("testcase_extract").format(context=context)
    response = llm.invoke(prompt)
    try:
        data = safe_json_loads(response.content)
        cases = data.get("test_cases", [])
        if not isinstance(cases, list):
            logger.warning("[testcase_extract] Invalid test_cases format")
            return []
        return cases
    except Exception as e:
        logger.error(f"[testcase_extract] Failed to parse JSON: {e}", exc_info=True)
        return []
