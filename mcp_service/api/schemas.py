from pydantic import BaseModel
from typing import Any, List, Dict, Optional

class PlanRequest(BaseModel):
    plan: str

class PlanResponse(BaseModel):
    results: List[Dict[str, Any]]
    error: Optional[str] = None

class RAGRequest(BaseModel):
    query: str
    limit: int = 5

class RAGResponse(BaseModel):
    success: bool
    results: List[Dict[str, Any]]
    total_results: int = 0
    error: Optional[str] = None

class DBRequest(BaseModel):
    query: str

class DBResponse(BaseModel):
    success: bool
    results: List[Dict[str, Any]]
    sql: Optional[str] = None
    row_count: int = 0
    error: Optional[str] = None

