"""
Final Answer Agent - Response Formatting
Generates user-facing answer using LangChain
"""
from langchain_core.prompts import ChatPromptTemplate
from graphs.state_schema import GraphState
from config.langchain_config import get_langchain_llm
from utils.logger import logger

# Initialize LangChain LLM
llm = get_langchain_llm(temperature=0.7)

# Create final answer prompt
final_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful AI assistant that provides clear, accurate answers based on provided context.

Guidelines:
- Answer directly and concisely
- Cite source types when relevant ([doc], [db], [web])
- If information is incomplete or uncertain, acknowledge it
- Use a professional but friendly tone
- Format responses with clear structure when appropriate"""),
    ("human", """User Question:
{query}

Context from Multiple Sources:
{context}

Provide the best possible answer:""")
])

def final_answer_agent(state: GraphState) -> GraphState:
    """
    Generates final user-facing answer from fused context or general response
    Includes conversation history for context-aware responses
    """
    query = state["query"]
    route = state.get("route", "rag")
    history = state.get("conversation_history", [])
    
    # For general route, use the direct response from general_agent
    if route == "general":
        general_response = state.get("general_response", "")
        if general_response:
            state["answer"] = general_response
            state.setdefault("debug", {})["answer_length"] = len(general_response)
            logger.info(f"[final_answer_agent] Using general response (length: {len(general_response)})")
            return state

    # For test route, use the prebuilt response from test_agent
    if route == "test":
        existing = state.get("answer", "")
        if existing:
            state.setdefault("debug", {})["answer_length"] = len(existing)
            logger.info("[final_answer_agent] Using test run response")
            return state
    
    # For other routes, use fused context with conversation history
    fused_context = state.get("fused_context") or ""
    
    # Build context string with history if available
    context_with_history = fused_context
    if history:
        history_text = "\n\nPrevious conversation:\n"
        for msg in history[-6:]:  # Last 3 exchanges
            role_label = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{role_label}: {msg['content']}\n"
        context_with_history = history_text + "\n" + fused_context
    
    try:
        logger.info(f"[final_answer_agent] Generating answer for route={route} with history")
        
        # Generate final answer using LangChain
        messages = final_prompt.format_messages(
            query=query,
            context=context_with_history
        )
        response = llm.invoke(messages)
        answer = response.content.strip()
        
        logger.info(f"[final_answer_agent] Generated answer (length: {len(answer)})")
        
        # Store in state
        state["answer"] = answer
        
        # Add metadata
        state.setdefault("debug", {})["answer_length"] = len(answer)
        state.setdefault("debug", {})["context_length"] = len(fused_context)
        state.setdefault("debug", {})["history_used"] = len(history)
        
    except Exception as e:
        logger.error(f"[final_answer_agent] Error generating answer: {e}", exc_info=True)
        # Fallback answer
        state["answer"] = "I apologize, but I encountered an error generating your answer. Please try rephrasing your question."
        state.setdefault("debug", {})["final_answer_error"] = str(e)
    
    return state
