import httpx
from graphs.state_schema import GraphState
from utils.helpers import load_prompt
from config.langchain_config import get_langchain_llm
from config.settings import settings
from utils.logger import logger
from langchain_core.prompts import ChatPromptTemplate

def web_agent(state: GraphState) -> GraphState:
    query = state["query"]
    plan_prompt_text = load_prompt("web").format(query=query)

    llm = get_langchain_llm(temperature=0.7)
    messages = [{"role": "system", "content": plan_prompt_text}]
    
    try:
        response = llm.invoke(messages)
        plan_str = response.content
        logger.info(f"[web_agent] LLM plan: {plan_str}")
    except Exception as e:
        logger.exception(f"[web_agent] LLM call failed: {e}")
        state["web_results"] = []  # type: ignore
        state.setdefault("debug", {})["web_error"] = str(e)
        return state

    try:
        # Web searches can take time - increase timeout to 60s
        with httpx.Client(timeout=60.0) as http_client:
            plan_resp = http_client.post(
                f"{settings.MCP_SERVICE_URL}/plan",
                json={"plan": plan_str},
            )
            plan_resp.raise_for_status()
            data = plan_resp.json()
    except httpx.ReadTimeout:
        logger.warning(f"[web_agent] MCP call timed out after 60s - web searches may be slow")
        data = {"results": [], "error": "timed out"}
    except Exception as e:
        logger.error(f"[web_agent] MCP call failed: {e}")
        data = {"results": [], "error": str(e)}

    state["web_results"] = data.get("results", [])  # type: ignore
    state.setdefault("debug", {})["web_plan"] = plan_str
    return state
