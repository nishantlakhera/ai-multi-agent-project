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
