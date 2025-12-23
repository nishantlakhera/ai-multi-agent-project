"""
DB Agent - Database Query Execution
Uses MCP service for secure SQL generation and execution
"""
import httpx
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from graphs.state_schema import GraphState
from config.langchain_config import get_langchain_llm
from config.settings import settings
from utils.logger import logger

# Initialize LangChain LLM
llm = get_langchain_llm(temperature=0.1)

def db_agent(state: GraphState) -> GraphState:
    """
    Executes database queries via MCP service with safety validations
    """
    query = state["query"]
    
    try:
        logger.info(f"[db_agent] Calling MCP service for query: {query}")
        
        # Call MCP service for database query
        with httpx.Client(timeout=30) as client:
            response = client.post(
                f"{settings.MCP_SERVICE_URL}/db",
                json={"query": query}
            )
            response.raise_for_status()
            data = response.json()
        
        if not data.get("success"):
            error_msg = data.get("error", "Unknown error")
            logger.warning(f"[db_agent] Query failed: {error_msg}")
            
            # Check if query was skipped (not relevant)
            if "Not database-related" in error_msg or data.get("skipped"):
                state["db_results"] = []
                state.setdefault("debug", {})["db_sql"] = "SKIPPED - not relevant"
            else:
                state["db_results"] = []
                state.setdefault("debug", {})["db_error"] = error_msg
                state.setdefault("debug", {})["db_sql"] = data.get("sql", "FAILED")
            
            return state
        
        results = data.get("results", [])
        sql = data.get("sql", "")
        row_count = data.get("row_count", 0)
        
        logger.info(f"[db_agent] Query successful: {row_count} rows returned")
        logger.info(f"[db_agent] SQL: {sql}")
        
        # Store results in state
        state["db_results"] = results
        state.setdefault("debug", {})["db_sql"] = sql
        state.setdefault("debug", {})["db_row_count"] = row_count
        
    except httpx.HTTPError as e:
        logger.error(f"[db_agent] MCP service HTTP error: {e}", exc_info=True)
        state["db_results"] = []
        state.setdefault("debug", {})["db_error"] = f"MCP service unavailable: {str(e)}"
        
    except Exception as e:
        logger.error(f"[db_agent] Unexpected error: {e}", exc_info=True)
        state["db_results"] = []
        state.setdefault("debug", {})["db_error"] = str(e)
    
    return state
