from typing import List, Optional, Dict, Any
from langchain_core.tools import tool
from duckduckgo_search import DDGS
import trafilatura
from trafilatura.settings import use_config
import wikipedia
import arxiv
import json


@tool
def web_search(query: str, max_results: int = 5, safe_search: str = "moderate") -> List[Dict[str, Any]]:
    """
    General web search using DuckDuckGo (no API key). Returns a list of results:
    [{title, href, body, source, published}]  (published may be None).
    Args:
        query: your search query
        max_results: number of results (1-50)
        safe_search: "off" | "moderate" | "strict"
    """

    results = []
    with DDGS() as ddgs:
        for i, r in enumerate(ddgs.text(query, max_results=max_results, safesearch=safe_search)):
            if i >= max_results:
                break
            results.append({
                "title": r.get("title"),
                "href": r.get("href"),
                "body": r.get("body"),
                "source": r.get("source"),
                "published": r.get("date") or r.get("published"),
            })

    if len(results)==0:
        results.append("No results found.")
    return results


@tool
def news_search(query: str, region: str = "wt-wt", max_results: int = 5) -> List[Dict[str, Any]]:
    """
    News search across many outlets via DuckDuckGo News (no API key).
    Args:
        query: news topic
        region: e.g., "wt-wt" (worldwide), "in-en" (India English), "us-en"
        max_results: number of news items (1-50)
    Returns: [{title, href, source, snippet, published, image, syndicate}]
    """

    items = []
    with DDGS() as ddgs:
        for i, r in enumerate(ddgs.news(query, region=region, max_results=max_results)):
            if i >= max_results:
                break
            items.append({
                "title": r.get("title"),
                "href": r.get("url") or r.get("href"),
                "source": r.get("source"),
                "snippet": r.get("excerpt") or r.get("body"),
                "published": r.get("date") or r.get("published"),
                "image": r.get("image"),
                "syndicate": r.get("syndicate"),
            })
    if len(items)==0:
        items.append("No results found.")
    return items

@tool
def read_url(url: str) -> Dict[str, Any]:
    """
    Fetches and cleans article text from a URL. Returns:
    {title, author, date, text, url}
    """
    
    if not url.startswith("https"):
        return {"error": "Only https links supported"}
    
    cfg = use_config()
    cfg.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")
    cfg.set("DEFAULT", "MIN_EXTRACTED_SIZE", "0")

    downloaded = trafilatura.fetch_url(url, no_ssl=True)
    if not downloaded:
        return {"url": url, "title": None, "author": None, "date": None, "text": None, "error": "fetch_failed"}

    data = trafilatura.extract(downloaded, include_comments=False, include_tables=False, with_metadata=True, config=cfg)
    if not data:
        return {"url": url, "title": None, "author": None, "date": None, "text": None, "error": "extract_failed"}

    
    json_data = trafilatura.extract(downloaded, with_metadata=True, output_format="json", config=cfg)
    
    meta = {}
    if json_data:
        try:
            meta = json.loads(json_data)
        except Exception:
            meta = {}

    return {
        "url": url,
        "title": meta.get("title"),
        "author": (meta.get("author", "") or meta.get("authors", "")),
        "date": meta.get("date") or meta.get("publication_date"),
        "text": meta.get("text"),
    }

@tool
def wikipedia_lookup(query: str, sentences: int = 5) -> Dict[str, Any]:
    """
    Returns a concise summary from Wikipedia plus the canonical URL.
    """
    
    wikipedia.set_lang("en")
    try:
        page_title = wikipedia.search(query, results=1)
        if not page_title:
            return {"title": None, "summary": None, "url": None}
        page = wikipedia.page(page_title[0], auto_suggest=False, redirect=True)
        summary = wikipedia.summary(page.title, sentences=sentences, auto_suggest=False, redirect=True)
        return {"title": page.title, "summary": summary, "url": page.url}
    except Exception as e:
        return {"title": None, "summary": None, "url": None, "error": str(e)}

@tool
def arxiv_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search arXiv for papers. Returns: [{title, authors, summary, pdf_url, published, primary_category}]
    """
    
    results = []
    search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)
    for r in search.results():
        results.append({
            "title": r.title,
            "authors": [a.name for a in r.authors],
            "summary": r.summary,
            "pdf_url": r.pdf_url,
            "published": r.published.isoformat() if r.published else None,
            "primary_category": r.primary_category,
        })
    if len(results)==0:
        results.append("No results found.")
    return results