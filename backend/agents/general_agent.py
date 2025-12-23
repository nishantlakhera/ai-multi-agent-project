"""
General Agent - Direct LLM responses for conversational and simple queries
Handles greetings, casual chat, math, and general knowledge without external tools
"""
from graphs.state_schema import GraphState
from config.langchain_config import get_langchain_llm
from utils.logger import logger
from langchain_core.prompts import ChatPromptTemplate

def general_agent(state: GraphState) -> GraphState:
    """
    Handles general conversational queries directly with LLM
    Includes conversation history for context-aware responses
    """
    query = state["query"]
    history = state.get("conversation_history", [])
    
    # Build conversation context
    system_msg = """You are a helpful AI assistant. Answer the user's question directly and concisely.
        
For greetings: Be friendly and brief.
For math: Calculate and show the answer.
For general knowledge: Provide accurate, concise information.
For casual chat: Respond naturally and helpfully.

Keep responses short (2-3 sentences) unless the question requires more detail.
Use conversation history to maintain context and remember previous exchanges."""
    
    # Create messages array with history
    messages = [{"role": "system", "content": system_msg}]
    
    # Add conversation history (last 5 exchanges)
    for msg in history[-10:]:  # Last 10 messages (5 exchanges)
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Add current query
    messages.append({"role": "user", "content": query})
    
    try:
        llm = get_langchain_llm(temperature=0.7)
        response = llm.invoke(messages)
        answer = response.content
        
        logger.info(f"[general_agent] Generated response with history (length: {len(answer)})")
        
        # Store the general response
        state["general_response"] = answer  # type: ignore
        
        # Add debug info
        state.setdefault("debug", {})["general_response_length"] = len(answer)
        state.setdefault("debug", {})["history_length"] = len(history)
        
    except Exception as e:
        logger.exception(f"[general_agent] Error: {e}")
        state["general_response"] = "I apologize, but I encountered an error. Please try again."  # type: ignore
        state.setdefault("debug", {})["general_error"] = str(e)
    
    return state
