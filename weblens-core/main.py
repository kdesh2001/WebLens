# tools_free_search.py
import time
from typing import List, Optional, Dict, Any
from langchain_core.tools import tool
from duckduckgo_search import DDGS
import trafilatura
from trafilatura.settings import use_config
import wikipedia
import arxiv
import json

from langchain_ollama import ChatOllama

llm = ChatOllama(
    model = "mistral:latest",
    validate_model_on_init = True,
    temperature = 0.3,
    num_predict = 65536,
    # other params ...
)

# --- 1) Web Search (DuckDuckGo: free, no key) ---
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

    print("******************************\nWeb search results:")
    # print(results)
    return results

# --- 2) News Search (DuckDuckGo News: free, no key) ---
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
    print("******************************\nNews search results:")
    # print(items)
    return items

# --- 3) URL Reader (Trafilatura: free, robust extraction) ---
@tool
def read_url(url: str) -> Dict[str, Any]:
    """
    Fetches and cleans article text from a URL. Returns:
    {title, author, date, text, url}
    """
    
    if not url.startswith("https"):
        return {"error": "Only https links supported"}
    
    cfg = use_config()
    # Grab more content, allow comments if needed
    cfg.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")
    cfg.set("DEFAULT", "MIN_EXTRACTED_SIZE", "0")

    downloaded = trafilatura.fetch_url(url, no_ssl=True)
    if not downloaded:
        return {"url": url, "title": None, "author": None, "date": None, "text": None, "error": "fetch_failed"}

    data = trafilatura.extract(downloaded, include_comments=False, include_tables=False, with_metadata=True, config=cfg)
    if not data:
        return {"url": url, "title": None, "author": None, "date": None, "text": None, "error": "extract_failed"}

    # Trafilatura returns JSON-ish string when with_metadata=True; use extract with metadata=True to get dict.
    # If your version returns a string, parse with `trafilatura.extract(..., output="json")`
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

# --- 4) Wikipedia quick lookup (free) ---
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

# --- 5) ArXiv search (free) ---
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
    return results

# -------------------------------------------------------------------------
import os
from getpass import getpass
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
import textwrap
from dotenv import load_dotenv
load_dotenv()

# from tools import web_search, news_search, wikipedia_lookup, read_url, arxiv_search

os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HUGGINGFACEHUB_API_TOKEN") or getpass("HF token: ")

@tool
def spl_func(n: int) -> int:
    """Special function tool. Takes int input, returns a value after applying the function"""
    return (2*n-1)**3

hf_llm = HuggingFaceEndpoint(
    repo_id="openai/gpt-oss-20b",
    task="text-generation",
    
    huggingfacehub_api_token=os.environ["HUGGINGFACEHUB_API_TOKEN"],
    max_new_tokens=65536,
    temperature=0.3,
)

chat_llm = ChatHuggingFace(llm=hf_llm)

SYSTEM_PROMPT = textwrap.dedent(
    '''
    You are an advanced AI agent powered by gpt-oss-20b. 
    You are given text passages or content from a web page. 
    Your task is to deeply analyze the passage, provide a clear summary, translate if needed, and verify any factual or research claims using the tools available. 
    You must always be accurate, concise, and evidence-based. Follow these rules strictly:

    TOOLS AVAILABLE:
    1. web_search(query: str)  
    - Use this for broad web lookups or general fact verification.  
    - Especially useful for claims not tied to recent news or research.  
    - Results may be brief; if insufficient, follow up with read_url on promising links.  

    2. news_search(query: str)  
    - Use this for fact-checking recent events or breaking news.  
    - Always cross-check multiple sources to confirm reliability.  
    - For detailed coverage, follow up with read_url.  
    - Use only if the given text looks like a recent event or something from news (not for general information).

    3. read_url(url: str)  
    - Use this to fetch full content from a reliable link when snippets are incomplete.  
    - Useful for in-depth context, news verification, or detailed analysis.  

    4. wikipedia_lookup(query: str)  
    - Use this for quick, encyclopedic background on well-known entities, concepts, events, or people.  
    - Prefer this for neutral summaries of established knowledge.  

    5. arxiv_search(query: str)  
    - Use this for claims related to research, technical concepts, or scientific topics.  
    - Prefer this for checking whether a research paper exists, summarizing findings, or providing context.  

    TEXT PROCESSING & SUMMARIZATION RULES:
    - Summarize the passage in 2-3 sentences, capturing only the key details.  
    - Be faithful to the original meaning. Do not distort or exaggerate.  
    - If the text is not in English:  
    • Short text → provide a full English translation.  
    • Long text → summarize in English.  
    - If the text contains statistics, structured data, or lists:  
    • Convert them into a clean, table-like structure.  
    - Avoid repetition, unnecessary details, or subjective interpretation.  

    FACT-CHECKING & CLAIM VERIFICATION RULES:
    - Detect factual statements, statistics, or claims in the passage.  
    - Verify them using the most relevant tool:  
    • web_search → general info, broad claims.  
    • news_search → recent news/events.  
    • wikipedia_lookup → encyclopedic background.  
    • arxiv_search → research/academic claims.  
    - Use read_url to gather complete information when snippets are insufficient.  
    - Always use multiple sources if possible.  
    - Explicitly label claims as:  
    • Verified (true),  
    • False (contradicted by sources), or  
    • Potentially misleading/unverified (conflicting or incomplete evidence).  

    OUTPUT REQUIREMENTS:
    - Provide a short, clear, and accurate summary of the passage.  
    - Translate or summarize in English if the original text is in another language.  
    - If data is present, present it in a clean table format.  
    - Explicitly state whether any claims in the passage are true, false, or misleading, citing evidence.  
    - Keep the response factual, precise, and to the point.  
    - Do not hallucinate. Only rely on tool results for factual verification.  
    '''
)

# PROMPT = textwrap.dedent(
#     """
#     You are an expert at text summarization. Read the following text carefully and produce a summary in no more than 2-3 sentences. Your summary must:

#     Capture the most crucial details and key information from the text.

#     Be a highly accurate and faithful representation of the original content without distortion or omission of critical facts.

#     Avoid unnecessary details, repetition, or subjective interpretation.

#     If the content is in any other language, translate it into English (return full translated content as it is for short text, for long text summarise it in English.)

#     If (and only if) the text contains any data, statistics or any information that can be represented well in a table, analyse the data and put it into a table like structure in your response.

#     Be concise, clear, and to the point.

#     Text: {text}
#     Summary:
#     """
# )

PROMPT = textwrap.dedent(
    '''
    Text: {text}
    Summary and detailed analysis:
    '''
)

agent = create_react_agent(llm, tools=[spl_func, web_search, news_search, read_url, wikipedia_lookup, arxiv_search], prompt=SYSTEM_PROMPT)

def invoke_agent(web_content: str):
    # conv = agent.invoke({"messages": [HumanMessage(content=PROMPT.format(text=web_content))]})
    # assistant_response = (conv["messages"][-1].content).split("assistantfinal")[-1]
    global agent
    events = agent.stream({"messages": [HumanMessage(content=PROMPT.format(text=web_content))]})

    final_answer = None
    for event in events:
        if "agent" in event:
            agent = event["agent"]
            if "messages" in agent:

                msg = agent["messages"][-1]
                # print("**************")
                # print(msg)
                # print("**************")
                if isinstance(msg, AIMessage):  # capture only assistant outputs
                    final_answer = msg.content
    assistant_response = final_answer.split("assistantfinal")[-1]
    return assistant_response

if __name__ == "__main__":
    web_content = "Rohit Gurunath Sharma is an Indian international cricketer and the captain of the India national team in ODIs. He is also a former captain in Tests and T20Is."
    # conv = agent.invoke({"messages": [HumanMessage(content=PROMPT.format(text=web_content))]})
    # conv = agent.invoke({"messages": [HumanMessage(content="What is the value of spl_func(4) and spl_func(6) ? Call the given spl_func() tool")]})
    # assistant_response = (conv["messages"][-1].content).split("assistantfinal")[-1]
    events = agent.stream({"messages": [HumanMessage(content=PROMPT.format(text=web_content))]})

    final_answer = None
    for event in events:
        print("****************************************")
        print(event)
        if "agent" in event:
            agent = event["agent"]
            if "messages" in agent:

                msg = agent["messages"][-1]
                # print("**************")
                # print(msg)
                # print("**************")
                if isinstance(msg, AIMessage):  # capture only assistant outputs
                    final_answer = msg.content
    assistant_response = final_answer.split("assistantfinal")[-1]
    
    # print(conv["messages"][-1].content)
    print(assistant_response)


    ''''
    analysisThe user: "What is the value of spl_func(4) and spl_func(6) ? Call the given spl_func() tool". The tool might return some function value. We need to call two times. We should produce two calls. Provide the values? The tool likely returns something like 343 for 4. Let's call for 6. We'll call again.assistantcommentary to=functions.spl_funcjson{"n":6}
    '''
