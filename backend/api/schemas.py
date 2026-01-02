from pydantic import BaseModel
from typing import Any, List, Dict, Optional

class ChatRequest(BaseModel):
    user_id: str
    message: str

class SourceAttribution(BaseModel):
    type: str
    meta: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    answer: str
    route: Optional[str] = None
    sources: Optional[List[SourceAttribution]] = None
    debug: Optional[Dict[str, Any]] = None

class TestRunRequest(BaseModel):
    query: str
    tags: Optional[List[str]] = None
    doc_filename: Optional[str] = None
    base_url: Optional[str] = None
    test_data: Optional[Dict[str, Any]] = None

class TestRunResponse(BaseModel):
    run_id: str

class TestRunStatusResponse(BaseModel):
    run: Dict[str, Any]
    steps: List[Dict[str, Any]]
    artifacts: List[Dict[str, Any]]

class RecordingConvertResponse(BaseModel):
    appended_cases: int
    doc_path: str
