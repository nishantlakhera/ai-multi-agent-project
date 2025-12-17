"""
RAG Agent - Retrieval-Augmented Generation
Uses MCP service for document search and LangChain for answer generation
"""
from typing import List
import httpx
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from graphs.state_schema import GraphState
from config.langchain_config import get_langchain_llm
from config.settings import settings
from utils.logger import logger

# Initialize LangChain LLM
llm = get_langchain_llm(temperature=0.3)

# Create RAG prompt template
rag_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="You answer strictly from provided context. If the context doesn't contain the answer, say 'I don't have enough information to answer that.'"),
    HumanMessage(content="Query: {query}\n\nContext:\n{context}\n\nProvide a clear, concise answer based only on the context above.")
])

def rag_agent(state: GraphState) -> GraphState:
    """
    Retrieves relevant documents via MCP service and generates answer
    """
    query = state["query"]
    
    try:
        # Call MCP service for RAG search
        logger.info(f"[rag_agent] Calling MCP service for query: {query}")
        
        with httpx.Client(timeout=30) as client:
            response = client.post(
                f"{settings.MCP_SERVICE_URL}/rag",
                json={"query": query, "limit": 5}
            )
            response.raise_for_status()
            data = response.json()
        
        if not data.get("success"):
            logger.error(f"[rag_agent] MCP search failed: {data.get('error')}")
            state["rag_results"] = []
            state.setdefault("debug", {})["rag_error"] = data.get("error")
            return state
        
        results = data.get("results", [])
        logger.info(f"[rag_agent] Retrieved {len(results)} documents")
        
        # Format context from results
        context_parts = []
        for idx, result in enumerate(results, 1):
            text = result.get("text", "")
            score = result.get("score", 0.0)
            metadata = result.get("metadata", {})
            context_parts.append(
                f"[Document {idx}] (Score: {score:.3f}, Source: {metadata})\n{text}"
            )
        
        context = "\n\n".join(context_parts) if context_parts else "NO_RELEVANT_DOCUMENTS"
        
        # Generate answer using LangChain
        messages = rag_prompt.format_messages(query=query, context=context)
        response = llm.invoke(messages)
        answer = response.content.strip()
        
        # Store results in state
        state["rag_results"] = results
        state.setdefault("debug", {})["rag_answer"] = answer
        state.setdefault("debug", {})["rag_context"] = context
        
        logger.info(f"[rag_agent] Generated answer (length: {len(answer)})")
        
    except httpx.HTTPError as e:
        logger.error(f"[rag_agent] MCP service HTTP error: {e}", exc_info=True)
        state["rag_results"] = []
        state.setdefault("debug", {})["rag_error"] = f"MCP service unavailable: {str(e)}"
        
    except Exception as e:
        logger.error(f"[rag_agent] Unexpected error: {e}", exc_info=True)
        state["rag_results"] = []
        state.setdefault("debug", {})["rag_error"] = str(e)
    
    return state

