"""
Test Agent - Triggers async test runs and returns run ID
"""
import re
from typing import Dict, Optional, List
from graphs.state_schema import GraphState
from config.settings import settings
from config.langchain_config import get_langchain_llm
from utils.helpers import load_prompt
from utils.json_utils import safe_json_loads
from services.test_run_service import start_test_run
from services.testcase_rag_service import retrieve_testcase_chunks
from utils.logger import logger

llm = get_langchain_llm(temperature=0.1)

def _extract_tags(query: str) -> List[str]:
    prompt = load_prompt("testcase_tags").format(query=query)
    try:
        response = llm.invoke(prompt)
        print(f" Tags extraction response: {response.content}")
        data = safe_json_loads(response.content)
        tags = data.get("tags", [])
        print(f" Extracted tags: {tags}")
        if isinstance(tags, list):
            return [str(t) for t in tags if str(t).strip()]
    except Exception:
        pass
    return []

def _extract_base_url(query: str) -> Optional[str]:
    match = re.search(r'(https?://[^\s,;]+)', query)
    return match.group(1) if match else None

def _extract_doc_filename(query: str) -> Optional[str]:
    match = re.search(r'\b(doc|file)\s*[:=]\s*([^\s,;]+)', query, re.IGNORECASE)
    return match.group(2) if match else None

def _extract_test_data(query: str) -> Dict[str, str]:
    pairs = re.findall(r'([A-Za-z0-9 _-]{2,})\s*[:=]\s*([^\s,;]+)', query)
    if not pairs:
        return {}
    reserved = {"doc", "file", "base_url", "url", "tags"}
    data: Dict[str, str] = {}
    for raw_key, raw_value in pairs:
        key = raw_key.strip().lower().replace(" ", "_")
        if key in reserved:
            continue
        data[key] = raw_value.strip()
    return data

def test_agent(state: GraphState) -> GraphState:
    query = state["query"]
    print(f" Query: {query}")
    tags = _extract_tags(query)
    print(f" Extracted tags: {tags}")
    base_url = _extract_base_url(query)
    print(f" Extracted base_url: {base_url}")
    doc_filename = _extract_doc_filename(query)
    print(f" Extracted doc_filename: {doc_filename}")
    test_data = _extract_test_data(query)
    print(f" Extracted test_data: {test_data}")

    chunks = retrieve_testcase_chunks(query, limit=settings.TEST_RAG_TOP_K, filename=doc_filename)
    print(f" Retrieved {len(chunks)} relevant chunks for test run.")
    if not chunks:
        message = (
            "No relevant test cases found. Ingest your test-case documents or "
            "specify a doc via `doc=YourDoc.docx`."
        )
        state["answer"] = message
        state.setdefault("debug", {})["test_run_skipped"] = True
        return state

    logger.info(f"[test_agent] Starting test run for query: {query}")
    if not doc_filename:
        message = (
            "Starting test run without a specific document. "
            "If no matching test case is found, ingest or specify a doc via "
            "`doc=YourDoc.docx`."
        )
        state.setdefault("debug", {})["test_doc_hint"] = message

    run_id = start_test_run(
        query=query,
        tags=tags or None,
        doc_filename=doc_filename,
        base_url=base_url,
        test_data_override=test_data or None,
    )

    message = f"Started test run {run_id}. Check status at /api/tests/{run_id}."
    if state.get("debug", {}).get("test_doc_hint"):
        message = f"{message} Note: {state['debug']['test_doc_hint']}"
    state["test_run_id"] = run_id
    state["answer"] = message
    state.setdefault("debug", {})["test_run_id"] = run_id
    state.setdefault("debug", {})["test_tags"] = tags
    if test_data:
        state.setdefault("debug", {})["test_data_override"] = test_data
    return state
