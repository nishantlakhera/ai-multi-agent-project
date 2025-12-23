from typing import Dict, Any
from tools.web_tool import execute_web_plan

def run_mcp_plan(plan: str) -> Dict[str, Any]:
    web_results = execute_web_plan(plan)
    return {
        "results": web_results
    }
