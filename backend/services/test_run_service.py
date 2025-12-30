from typing import Dict, Any, Optional, List
import threading
import uuid
import re
import httpx
from config.settings import settings
from utils.logger import logger
from services.testcase_rag_service import retrieve_testcase_chunks, format_context
from services.testcase_extraction_service import extract_test_cases
from services.testcase_selection_service import select_best_case
from services.testcase_dsl_service import generate_test_dsl
from services.test_run_store import test_run_store

def start_test_run(
    query: str,
    tags: Optional[List[str]] = None,
    doc_filename: Optional[str] = None,
    base_url: Optional[str] = None,
    test_data_override: Optional[Dict[str, Any]] = None,
) -> str:
    run_id = str(uuid.uuid4())
    test_run_store.create_run(run_id, {
        "query": query,
        "doc_filename": doc_filename or "",
        "tags": ",".join(tags or []),
    })

    thread = threading.Thread(
        target=_run_flow,
        args=(run_id, query, tags, doc_filename, base_url, test_data_override),
        daemon=True,
    )
    thread.start()
    return run_id

def get_test_run(run_id: str) -> Dict[str, Any]:
    return test_run_store.get_run(run_id)

def _extract_test_data_from_case(test_case: Dict[str, Any]) -> Dict[str, str]:
    data = test_case.get("test_data")
    if isinstance(data, dict):
        return {str(k).strip().lower(): str(v).strip() for k, v in data.items()}

    parsed: Dict[str, str] = {}
    if isinstance(data, list):
        for item in data:
            if not isinstance(item, str):
                continue
            match = re.match(r'\s*([^:=]+)\s*[:=]\s*(.+)\s*', item)
            if match:
                key = match.group(1).strip().lower().replace(" ", "_")
                parsed[key] = match.group(2).strip()
    return parsed

def _run_flow(
    run_id: str,
    query: str,
    tags: Optional[List[str]],
    doc_filename: Optional[str],
    base_url: Optional[str],
    test_data_override: Optional[Dict[str, Any]],
):
    try:
        test_run_store.update_status(run_id, "running")

        chunks = retrieve_testcase_chunks(query, limit=settings.TEST_RAG_TOP_K, filename=doc_filename)
        logger.info(f"[test_run_service] Retrieved {len(chunks)} relevant chunks for test run.")
        context = format_context(chunks)
        print(f" Formatted context for test run: {context}...")
        if not chunks:
            test_run_store.update_status(
                run_id,
                "failed",
                error="No relevant test cases found. Ingest the doc or pass doc=YourDoc.docx",
            )
            return

        cached = test_run_store.get_cached_catalog(doc_filename or "default")
        if cached and cached.get("test_cases"):
            cases = cached["test_cases"]
        else:
            cases = extract_test_cases(context)
            test_run_store.cache_catalog(doc_filename or "default", {"test_cases": cases})

        test_case = select_best_case(cases, query, tags)
        print(f" Selected test case for run: {test_case}")
        if not test_case:
            test_run_store.update_status(
                run_id,
                "failed",
                error="No matching test case found. Ingest the doc or pass doc=YourDoc.docx",
            )
            return

        case_data = _extract_test_data_from_case(test_case)
        merged_data: Dict[str, Any] = dict(case_data)
        if test_data_override:
            for key, value in test_data_override.items():
                if key not in merged_data or not merged_data.get(key):
                    merged_data[key] = value

        dsl = generate_test_dsl(
            test_case,
            base_url=base_url,
            test_data=merged_data or None,
        )
        print(f" Generated test DSL for run: {dsl}")
        if not dsl.get("steps"):
            test_run_store.update_status(run_id, "failed", error="Generated DSL is empty")
            return

        payload = {"run_id": run_id, "plan": dsl}
        with httpx.Client(timeout=120) as client:
            response = client.post(f"{settings.MCP_SERVICE_URL}/tests/run", json=payload)
            response.raise_for_status()
            result = response.json()

        for step in result.get("steps", []):
            test_run_store.add_step(run_id, step)
        for artifact in result.get("artifacts", []):
            test_run_store.add_artifact(run_id, artifact)

        status = "passed" if result.get("status") == "passed" else "failed"
        test_run_store.update_status(
            run_id,
            status,
            error=result.get("error"),
            failed_step=result.get("failed_step"),
        )

    except Exception as e:
        logger.error(f"[test_run_service] Run failed: {e}", exc_info=True)
        test_run_store.update_status(run_id, "failed", error=str(e))
