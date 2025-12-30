# Test Agent Guide

This document explains the test agent architecture, data flow, and how the system
executes doc-driven test cases with Playwright via the MCP service.

## Overview

The test agent lets you trigger UI test cases from chat. It retrieves test cases
from a dedicated Qdrant collection, converts them into a deterministic Test DSL,
and executes the DSL in the MCP service using Playwright. Results are stored in
Redis and can be polled via the API.

## High-Level Architecture

```
                    +--------------------+
                    |       Client       |
                    |  (Chat / Frontend) |
                    +----------+---------+
                               |
                               v
                    +--------------------+
                    |   Backend API      |
                    |  /api/chat         |
                    |  /api/tests/*      |
                    +----+-----------+---+
                         |           |
                         |           +------------------------------+
                         |                                          |
                         v                                          v
                +-----------------+                        +-----------------+
                | LangGraph       |                        | Redis           |
                | Router -> Test  |                        | Test Run Store  |
                +--------+--------+                        +-----------------+
                         |
                         v
                +-----------------+          +-----------------------+
                | Test Run Service|          | Qdrant (test_cases)   |
                | - RAG retrieval |<-------->| Test Case Chunks      |
                | - Extraction    |          +-----------------------+
                | - DSL generation|
                +--------+--------+
                         |
                         v
                +--------------------------+
                | MCP Service              |
                | /tests/run               |
                | Playwright DSL execution |
                +--------------------------+
                         |
                         v
                +--------------------------+
                | Browser + Screenshots    |
                +--------------------------+
```

## Data Flow (End-to-End)

1) User triggers a test in chat:
   - Example: "run registration test doc=test_case_template.docx"

2) Router sends the query to the test agent.

3) Test agent performs a quick RAG lookup:
   - If no relevant chunks are found, it returns a friendly error and does not
     start a run.

4) Test run service:
   - Retrieves relevant test case chunks from Qdrant (test_cases collection).
   - Extracts structured test cases (scenario, steps, test_data, expected, tags).
   - Selects the best matching case.
   - Generates a deterministic Test DSL (JSON).

5) MCP Playwright runner:
   - Executes the DSL steps.
   - Captures screenshots and step logs.
   - Returns results to the backend.

6) Backend stores run status and artifacts in Redis.

7) Client polls /api/tests/{run_id} for status and logs.

## Block Diagram (End-to-End Data Flow)

```
 [User Query]
      |
      v
 [Backend /api/chat]
      |
      v
 [LangGraph Router] ---> [Test Agent Pre-check (RAG)]
      |                          |
      |                          v
      |                   [No Chunks? -> Fail Fast]
      v
 [Test Run Service]
      |
      v
 [Qdrant test_cases]
      |
      v
 [LLM Extract -> Test Cases]
      |
      v
 [Select Best Case]
      |
      v
 [LLM -> Test DSL (Domain Specific Language)]
      |
      v
 [MCP /tests/run]
      |
      v
 [Playwright Execution]
      |
      v
 [Screenshots + Step Logs]
      |
      v
 [Redis Test Run Store]
      |
      v
 [Client Polls /api/tests/{run_id}]
```

## Test Case Format (Doc Template)

Use a table with these columns:
- Scenario
- Test Steps
- Test Data
- Expected
- Tags

Guidelines:
- Use one row per test case.
- Separate steps and expected outcomes with new lines.
- Use key: value pairs in Test Data.
- Add explicit selectors in steps where UI is ambiguous.

Example step lines:
- Goto https://qa.thermofisher.com
- Click Sign in toggle (selector: css=#sign-in-toggle)
- Click Sign in link (selector: css=li#sign-in .cmp-ctaitem__anchor)

## Test DSL (Generated)

The DSL is JSON with a list of steps. Allowed actions:
- goto
- click
- fill
- select
- assert_visible
- assert_text
- screenshot

Each step includes a "target" (selector) and optional "value".

Example:
```
{
  "name": "Example Test",
  "base_url": "https://qa.thermofisher.com",
  "steps": [
    {"action": "goto", "target": "/"},
    {"action": "click", "target": "css=#sign-in-toggle"},
    {"action": "click", "target": "css=li#sign-in .cmp-ctaitem__anchor"},
    {"action": "fill", "target": "label=\"Email\"", "value": "user@example.com"},
    {"action": "fill", "target": "label=\"Password\"", "value": "Secret123"},
    {"action": "click", "target": "role=button name=\"Sign in\""}
  ]
}
```

## Collections and Storage

- Test cases are stored in Qdrant collection: `test_cases`
- Other docs can remain in `documents`
- Test run status, steps, and artifacts are stored in Redis

## Key Files

- Test agent: `backend/agents/test_agent.py`
- Test run orchestration: `backend/services/test_run_service.py`
- RAG retrieval: `backend/services/testcase_rag_service.py`
- DSL generation: `backend/services/testcase_dsl_service.py`
- MCP Playwright runner: `mcp_service/tools/playwright_tool.py`
- Test prompts: `backend/prompts/testcase_extract.txt`, `backend/prompts/testcase_dsl.txt`

## Recommended Run Steps

1) Ingest test case docs into the test_cases collection:
   - `PYTHONPATH=. python -m embeddings.docx_ingestion_pipeline`

2) Trigger a test from chat:
   - "run registration test doc=test_case_template.docx"

3) Poll for status:
   - `GET /api/tests/{run_id}`

4) Review screenshots in:
   - `logs/test_runs/{run_id}/` (MCP working directory)

## Notes

- If the UI uses toggles/menus, include explicit selectors in the test steps.
- If a locator is ambiguous, prefer CSS selectors or data-testid attributes.
- If no test cases are ingested, the test agent returns an error immediately.
