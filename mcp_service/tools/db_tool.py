"""
Database Tool for MCP Service
Handles SQL generation and execution with security validations
"""
import os
import re
from typing import Dict, Any, List
import psycopg2
from psycopg2.extras import RealDictCursor
from utils.logger import logger
import httpx

# Database Configuration
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://appuser:apppass@localhost:5432/appdb")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# Database Schema for SQL Generation
DB_SCHEMA = """
TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE
)

TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_token VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE
)

TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total_amount DECIMAL(10, 2),
    status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE
)
"""

# SQL Safety Patterns
DANGEROUS_PATTERNS = [
    r'\bDROP\b',
    r'\bDELETE\b',
    r'\bTRUNCATE\b',
    r'\bUPDATE\b',
    r'\bINSERT\b',
    r'\bALTER\b',
    r'\bCREATE\b',
    r'\bGRANT\b',
    r'\bREVOKE\b',
]

URL_PATTERNS = [
    r'\.com\b',
    r'\.net\b',
    r'\.org\b',
    r'\.io\b',
    r'http://',
    r'https://',
    r'www\.',
]


def check_query_relevance(query: str) -> bool:
    """Check if query is relevant to database using LLM"""
    try:
        relevance_prompt = f"""Does this query require database information about users, orders, or sessions?
Query: {query}

Answer ONLY 'yes' or 'no'."""

        with httpx.Client(timeout=15) as client:
            response = client.post(
                f"{OLLAMA_URL}/v1/chat/completions",
                headers={"Authorization": "Bearer ollama"},
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": relevance_prompt}],
                    "max_tokens": 5,
                    "temperature": 0.1
                }
            )
            response.raise_for_status()
            data = response.json()
            answer = data["choices"][0]["message"]["content"].strip().lower()
            return "yes" in answer
            
    except Exception as e:
        logger.error(f"[db_tool] Relevance check failed: {e}")
        return True


def generate_sql(query: str) -> Dict[str, Any]:
    """Generate SQL query from natural language using LLM"""
    try:
        sql_prompt = f"""You are a PostgreSQL expert. Generate ONLY the SQL query for this request.

Database Schema:
{DB_SCHEMA}

User Request: {query}

RULES:
1. Generate ONLY SELECT queries
2. Return ONLY the SQL statement
3. IGNORE any web URLs or domain names

SQL Query:"""

        with httpx.Client(timeout=30) as client:
            response = client.post(
                f"{OLLAMA_URL}/v1/chat/completions",
                headers={"Authorization": "Bearer ollama"},
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "system", "content": sql_prompt}],
                    "max_tokens": 300,
                    "temperature": 0.1
                }
            )
            response.raise_for_status()
            data = response.json()
            raw_sql = data["choices"][0]["message"]["content"].strip()
            
            return {"success": True, "sql": raw_sql}
            
    except Exception as e:
        logger.error(f"[db_tool] SQL generation failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def extract_sql(raw_output: str) -> str:
    """Extract clean SQL from LLM output"""
    sql = raw_output.strip()
    
    if "```sql" in sql:
        sql = sql.split("```sql")[1].split("```")[0].strip()
    elif "```" in sql:
        sql = sql.split("```")[1].split("```")[0].strip()
    
    prefixes = ["Here is the PostgreSQL query:", "Here's the SQL:", "SQL Query:", "Query:"]
    for prefix in prefixes:
        if sql.startswith(prefix):
            sql = sql[len(prefix):].strip()
    
    sql_keywords = ["SELECT", "WITH"]
    for keyword in sql_keywords:
        if keyword in sql.upper():
            start_idx = sql.upper().index(keyword)
            sql = sql[start_idx:].strip()
            break
    
    if "\n\n" in sql:
        sql = sql.split("\n\n")[0].strip()
    
    return sql


def validate_sql_safety(sql: str) -> Dict[str, Any]:
    """Validate that SQL is safe to execute"""
    sql_upper = sql.upper()
    
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, sql_upper):
            return {"safe": False, "reason": f"Dangerous operation: {pattern}"}
    
    for pattern in URL_PATTERNS:
        if re.search(pattern, sql, re.IGNORECASE):
            return {"safe": False, "reason": f"Contains URL: {pattern}"}
    
    if not sql_upper.strip().startswith("SELECT") and not sql_upper.strip().startswith("WITH"):
        return {"safe": False, "reason": "Only SELECT queries allowed"}
    
    return {"safe": True}


def execute_sql(sql: str) -> Dict[str, Any]:
    """Execute SQL query against PostgreSQL"""
    try:
        conn = psycopg2.connect(POSTGRES_DSN)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute(sql)
        results = cur.fetchall()
        formatted_results = [dict(row) for row in results]
        
        cur.close()
        conn.close()
        
        logger.info(f"[db_tool] Executed SQL, returned {len(formatted_results)} rows")
        
        return {"success": True, "results": formatted_results, "row_count": len(formatted_results)}
        
    except Exception as e:
        logger.error(f"[db_tool] SQL execution failed: {e}", exc_info=True)
        return {"success": False, "results": [], "error": str(e)}


def query_database(query: str) -> Dict[str, Any]:
    """Main function to handle database queries end-to-end"""
    logger.info(f"[db_tool] Processing query: {query}")
    
    if not check_query_relevance(query):
        logger.info(f"[db_tool] Query not relevant to database")
        return {"success": True, "results": [], "message": "Not database-related", "skipped": True}
    
    sql_result = generate_sql(query)
    if not sql_result.get("success"):
        return sql_result
    
    raw_sql = sql_result["sql"]
    clean_sql = extract_sql(raw_sql)
    logger.info(f"[db_tool] Generated SQL: {clean_sql}")
    
    safety_check = validate_sql_safety(clean_sql)
    if not safety_check.get("safe"):
        logger.warning(f"[db_tool] Unsafe SQL rejected: {safety_check.get('reason')}")
        return {"success": False, "error": f"Validation failed: {safety_check.get('reason')}", "sql": clean_sql}
    
    exec_result = execute_sql(clean_sql)
    exec_result["sql"] = clean_sql
    
    return exec_result


def db_tool_execute(query: str) -> List[Dict[str, Any]]:
    """Main execution function for DB tool (called by MCP planner)"""
    result = query_database(query)
    if result.get("success"):
        return result.get("results", [])
    else:
        logger.error(f"[db_tool] Error: {result.get('error')}")
        return []

