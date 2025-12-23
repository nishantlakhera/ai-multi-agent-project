"""
Fusion Agent - Multi-Source Result Synthesis
Combines RAG, DB, and Web results using LangChain
"""
from langchain_core.prompts import ChatPromptTemplate
from graphs.state_schema import GraphState
from config.langchain_config import get_langchain_llm
from utils.logger import logger

# Initialize LangChain LLM
llm = get_langchain_llm(temperature=0.5)

# Create fusion prompt
fusion_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert at synthesizing information from multiple sources. Combine the provided data into a coherent, comprehensive context."),
    ("human", """Synthesize the following information sources:

RAG Documents:
{rag_context}

Database Results:
{db_context}

Web Search Results:
{web_context}

Create a unified, structured summary that:
1. Identifies key information from each source
2. Resolves any conflicts between sources
3. Prioritizes the most reliable information
4. Maintains source attribution

Synthesized Context:""")
])

def fusion_agent(state: GraphState) -> GraphState:
    """
    Intelligently combines results from multiple agents
    """
    query = state["query"]
    rag_results = state.get("rag_results") or []
    db_results = state.get("db_results") or []
    web_results = state.get("web_results") or []
    
    # Format RAG context
    rag_context = "None"
    if rag_results:
        snippets = []
        for idx, r in enumerate(rag_results, 1):
            text = r.get("text", "") or r.get("payload", {}).get("text", "") or r.get("payload", {}).get("content", "")
            score = r.get("score", 0.0)
            snippets.append(f"[Doc {idx}] (Score: {score:.3f})\n{text}")
        rag_context = "\n---\n".join(snippets)
    
    # Format DB context
    db_context = "None"
    if db_results:
        db_context = f"Query returned {len(db_results)} rows:\n{db_results}"
    
    # Format Web context
    web_context = "None"
    if web_results:
        web_context = f"Search results:\n{web_results}"
    
    # If only one source has data, skip LLM fusion
    sources_with_data = sum([bool(rag_results), bool(db_results), bool(web_results)])
    
    if sources_with_data <= 1:
        # Simple concatenation for single source
        fused = "\n\n".join([
            f"RAG: {rag_context}" if rag_results else "",
            f"DB: {db_context}" if db_results else "",
            f"WEB: {web_context}" if web_results else ""
        ]).strip() or "NO_CONTEXT"
        
        logger.info(f"[fusion_agent] Single source, simple fusion (length: {len(fused)})")
    else:
        # Use LLM to intelligently synthesize multiple sources
        try:
            logger.info(f"[fusion_agent] Fusing {sources_with_data} sources with LLM")
            messages = fusion_prompt.format_messages(
                rag_context=rag_context,
                db_context=db_context,
                web_context=web_context
            )
            response = llm.invoke(messages)
            fused = response.content.strip()
            logger.info(f"[fusion_agent] LLM fusion complete (length: {len(fused)})")
            
        except Exception as e:
            logger.error(f"[fusion_agent] LLM fusion failed: {e}", exc_info=True)
            # Fallback to simple concatenation
            fused = "\n\n".join([
                f"RAG: {rag_context}" if rag_results else "",
                f"DB: {db_context}" if db_results else "",
                f"WEB: {web_context}" if web_results else ""
            ]).strip() or "NO_CONTEXT"
    
    state["fused_context"] = fused
    return state
