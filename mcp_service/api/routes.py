from fastapi import APIRouter
from api.schemas import PlanRequest, PlanResponse, RAGRequest, RAGResponse, DBRequest, DBResponse, TestRunRequest, TestRunResponse
from planner.mcp_planner import run_mcp_plan
from tools.rag_tool import search_documents
from tools.db_tool import query_database
from tools.playwright_tool import run_dsl_plan

router = APIRouter()

@router.post("/plan", response_model=PlanResponse)
def plan(req: PlanRequest):
    try:
        data = run_mcp_plan(req.plan)
        return PlanResponse(results=data.get("results", []))
    except Exception as e:
        return PlanResponse(results=[], error=str(e))

@router.post("/rag", response_model=RAGResponse)
def rag_search(req: RAGRequest):
    """
    Execute RAG (Retrieval-Augmented Generation) search
    Searches vector database for relevant documents
    """
    try:
        result = search_documents(req.query, req.limit)
        return RAGResponse(
            success=result.get("success", False),
            results=result.get("results", []),
            total_results=result.get("total_results", 0),
            error=result.get("error")
        )
    except Exception as e:
        return RAGResponse(
            success=False,
            results=[],
            error=str(e)
        )

@router.post("/db", response_model=DBResponse)
def db_query(req: DBRequest):
    """
    Execute database query with natural language
    Generates and executes SQL with safety validations
    """
    try:
        result = query_database(req.query)
        return DBResponse(
            success=result.get("success", False),
            results=result.get("results", []),
            sql=result.get("sql"),
            row_count=result.get("row_count", 0),
            error=result.get("error")
        )
    except Exception as e:
        return DBResponse(
            success=False,
            results=[],
            error=str(e)
        )

@router.post("/tests/run", response_model=TestRunResponse)
def run_tests(req: TestRunRequest):
    """
    Execute Playwright DSL plan and return result
    """
    try:
        result = run_dsl_plan(req.plan, req.run_id)
        return TestRunResponse(**result)
    except Exception as e:
        return TestRunResponse(status="failed", error=str(e), steps=[], artifacts=[])

@router.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mcp"}
