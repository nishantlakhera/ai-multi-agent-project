from typing import TypedDict, List, Literal, Any, Optional

Route = Literal["rag", "db", "web", "multi", "general", "test"]

class GraphState(TypedDict, total=False):
    user_id: str
    query: str
    conversation_history: List[dict]
    route: Optional[Route]
    rag_results: List[dict]
    db_results: List[dict]
    web_results: List[dict]
    general_response: str
    fused_context: str
    answer: str
    test_run_id: str
    debug: dict
