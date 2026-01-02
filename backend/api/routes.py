from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from api.schemas import ChatRequest, ChatResponse, SourceAttribution, TestRunRequest, TestRunResponse, TestRunStatusResponse, RecordingConvertResponse
from graphs.multi_agent_graph import graph_app
from graphs.state_schema import GraphState
from services.memory_service import memory_service
from services.test_run_service import start_test_run, get_test_run
from services.recording_conversion_service import convert_recordings

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # Get conversation history
    history = memory_service.get_history(req.user_id, limit=5)
    # print(f"printing history {history}")# Last 5 exchanges
    
    # Add current user message to memory
    memory_service.add_message(req.user_id, "user", req.message)

    # Build initial state with history context
    init_state: GraphState = {
        "user_id": req.user_id,
        "query": req.message,
        "conversation_history": history,  # type: ignore
    }

    final_state = graph_app.invoke(init_state)
    print(f"printing final state {final_state}")

    answer = final_state.get("answer", "")
    route = final_state.get("route")
    debug = final_state.get("debug", {})

    sources: list[SourceAttribution] = []

    if final_state.get("rag_results"):
        sources.append(SourceAttribution(type="rag"))
    if final_state.get("db_results"):
        sources.append(SourceAttribution(type="db"))
    if final_state.get("web_results"):
        sources.append(SourceAttribution(type="web"))

    memory_service.add_message(req.user_id, "assistant", answer)

    return ChatResponse(
        answer=answer,
        route=route,
        sources=sources or None,
        debug=debug or None,
    )

@router.get("/history/{user_id}")
def get_history(user_id: str, limit: int = 10):
    """
    Get conversation history for a user
    
    Note: Conversations are automatically deleted after 30 days of inactivity
    """
    history = memory_service.get_history(user_id, limit=limit)
    return {"user_id": user_id, "history": history, "count": len(history)}

@router.delete("/history/{user_id}")
def clear_history(user_id: str):
    """Clear all conversation history for a specific user"""
    memory_service.clear_history(user_id)
    return {"status": "success", "message": f"History cleared for user {user_id}"}

@router.post("/admin/cleanup-history")
def cleanup_old_history(days: int = 30):
    """
    Admin endpoint: Delete conversations older than specified days
    Default: 30 days
    
    This should be called periodically (e.g., daily cron job)
    """
    deleted_count = memory_service.cleanup_old_conversations(days=days)
    return {
        "status": "success",
        "deleted_count": deleted_count,
        "message": f"Deleted conversations older than {days} days"
    }

@router.post("/tests/run", response_model=TestRunResponse)
def run_test(req: TestRunRequest):
    run_id = start_test_run(
        query=req.query,
        tags=req.tags,
        doc_filename=req.doc_filename,
        base_url=req.base_url,
        test_data_override=req.test_data,
    )
    return TestRunResponse(run_id=run_id)

@router.get("/tests/{run_id}", response_model=TestRunStatusResponse)
def get_test_status(run_id: str):
    return get_test_run(run_id)

@router.post("/tests/record/convert", response_model=RecordingConvertResponse)
async def convert_recordings_to_docx(
    recordings: list[UploadFile] = File(...),
    doc_path: str = Form(...),
    scenario_prefix: str | None = Form(default=None),
    expected: str | None = Form(default=None),
    tags: str | None = Form(default=None),
):
    if not recordings:
        raise HTTPException(status_code=400, detail="No recordings provided")

    contents: list[tuple[str, str]] = []
    for recording in recordings:
        raw = await recording.read()
        text = raw.decode("utf-8", errors="ignore")
        contents.append((recording.filename or "recording", text))

    tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
    appended = convert_recordings(
        recordings=contents,
        doc_path=doc_path,
        scenario_prefix=scenario_prefix,
        expected=expected,
        tags=tag_list or None,
    )
    return RecordingConvertResponse(appended_cases=appended, doc_path=doc_path)
