"""
Router Agent - Query Classification and Routing
"""
from graphs.state_schema import GraphState
from utils.helpers import load_prompt
from config.langchain_config import get_langchain_llm
from utils.logger import logger
import re

# Initialize LangChain LLM
llm = get_langchain_llm(temperature=0.1)

def router_agent(state: GraphState) -> GraphState:
    """
    Analyzes query and routes to appropriate agent(s)
    """
    query = state["query"]
    query_lower = query.lower()
    
    try:
        # Load routing prompt
        prompt_text = load_prompt("router").format(query=query)
        
        # Get LLM response (simplified - just the route word)
        logger.info(f"[router_agent] Analyzing query: {query}")
        response = llm.invoke(prompt_text)
        
        # Extract route from response (should be one word: rag, db, web, multi, or general)
        route_text = response.content.strip().lower()
        
        # Find the route word in the response
        if "test" in route_text:
            route = "test"
            confidence = 0.9
        elif "general" in route_text:
            route = "general"
            confidence = 0.9
        elif "multi" in route_text:
            route = "multi"
            confidence = 0.9
        elif "web" in route_text:
            route = "web"
            confidence = 0.9
        elif "db" in route_text or "database" in route_text:
            route = "db"
            confidence = 0.9
        elif "rag" in route_text or "document" in route_text:
            route = "rag"
            confidence = 0.9
        else:
            # Fallback to heuristic
            route = heuristic_fallback(query_lower)
            confidence = 0.5
            logger.warning(f"[router_agent] Unclear response, using heuristic: {route}")
        
        if route != "test" and re.search(r"^\s*(run|execute|trigger)\b", query_lower):
            if re.search(r"\b(sql|database|db)\b", query_lower):
                route = "db"
                confidence = max(confidence, 0.7)
            elif re.search(r"(https?://|\.com\b|\.org\b|\.net\b|\.io\b)", query_lower):
                route = "web"
                confidence = max(confidence, 0.7)
            else:
                route = "test"
                confidence = max(confidence, 0.7)

        logger.info(f"[router_agent] Decision: {route} (confidence: {confidence:.2f})")
        
        # Store debug info
        state.setdefault("debug", {})["router_confidence"] = confidence
        state.setdefault("debug", {})["router_reasoning"] = route_text[:200]
        
    except Exception as e:
        logger.error(f"[router_agent] LLM call failed: {e}", exc_info=True)
        # Fallback to heuristic routing
        route = heuristic_fallback(query_lower)
        logger.warning(f"[router_agent] Using heuristic fallback: {route}")
    
    logger.info(f"[router_agent] Final route={route} for query={query!r}")
    
    state["route"] = route
    return state


def heuristic_fallback(query_lower: str) -> str:
    """
    Fallback heuristic routing when LLM fails
    """
    # Check for multi-source indicators
    if " and " in query_lower and len(query_lower.split(" and ")) == 2:
        has_url = bool(re.search(r'\.(com|org|net|io|ai|co)', query_lower))
        has_db = bool(re.search(r'\b(how many|count|total|list|show|users?|orders?)\b', query_lower))
        if has_url and has_db:
            return "multi"
    
    # Check for test keywords
    if re.search(r'\b(run|execute|trigger)\b.*\b(test|tests|testcase|test case|playwright|automation)\b', query_lower):
        return "test"

    # Check for database keywords
    if re.search(r'\b(how many|count|total|users?|orders?|sessions?|database|sql)\b', query_lower):
        return "db"
    
    # Check for web keywords
    if re.search(r'\b(latest|news|search|website|\.com|\.net|\.org|http)\b', query_lower):
        return "web"
    
    # Default to RAG for documentation queries
    return "rag"
