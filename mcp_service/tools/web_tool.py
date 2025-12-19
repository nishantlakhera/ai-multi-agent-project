from typing import List, Dict, Any
import httpx
import json
from bs4 import BeautifulSoup
from utils.logger import logger

def search_duckduckgo(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search using DuckDuckGo HTML scraping (no API key required).
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        url = f"https://html.duckduckgo.com/html/?q={query}"

        with httpx.Client(timeout=20.0) as client:
            response = client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        for result in soup.find_all("div", class_="result", limit=max_results):
            try:
                title_elem = result.find("a", class_="result__a")
                snippet_elem = result.find("a", class_="result__snippet")

                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get("href", "")
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                    results.append({
                        "url": url,
                        "title": title,
                        "snippet": snippet,
                    })
            except Exception as e:
                logger.warning(f"Error parsing search result: {e}")
                continue

        return results
    except Exception as e:
        logger.error(f"DuckDuckGo search failed: {e}")
        return []

def fetch_url_content(url: str, max_length: int = 2000) -> str:
    """
    Fetch and extract text content from a URL.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        with httpx.Client(timeout=20.0) as client:
            response = client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Get text
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text[:max_length]
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return ""

def execute_web_plan(plan: str) -> List[Dict[str, Any]]:
    """
    Execute web search based on LLM plan.
    Extracts search queries from JSON plan and performs web searches.
    """
    logger.info(f"Executing web plan: {plan[:100]}...")

    # Extract JSON from markdown code blocks if present
    plan_text = plan.strip()
    if "```json" in plan_text:
        start = plan_text.find("```json") + 7
        end = plan_text.find("```", start)
        plan_text = plan_text[start:end].strip()
    elif "```" in plan_text:
        start = plan_text.find("```") + 3
        end = plan_text.find("```", start)
        plan_text = plan_text[start:end].strip()

    # Try to parse as JSON
    queries = []
    try:
        plan_data = json.loads(plan_text)
        queries = plan_data.get("queries", [])
        if not queries and "query" in plan_data:
            queries = [plan_data["query"]]
    except json.JSONDecodeError:
        logger.warning("Failed to parse plan as JSON, using as direct query")
        queries = [plan_text[:200]]

    # If no queries found, use the plan text itself
    if not queries:
        queries = [plan_text[:200]]

    # Perform searches for all queries
    all_results = []
    for query in queries[:3]:  # Limit to 3 queries
        results = search_duckduckgo(query, max_results=3)

    # Perform searches for all queries
    all_results = []
    for query in queries[:3]:  # Limit to 3 queries
        results = search_duckduckgo(query, max_results=3)
        
        # Fetch content from top result
        for result in results[:1]:  # Only fetch content from top result per query
            if result.get("url"):
                content = fetch_url_content(result["url"], max_length=1000)
                if content:
                    result["content"] = content
        
        all_results.extend(results)

    logger.info(f"Web search returned {len(all_results)} results")
    return all_results
