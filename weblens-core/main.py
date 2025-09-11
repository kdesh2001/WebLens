from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
import textwrap
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.1,
    max_tokens=None,
    timeout=None,
    reasoning_format="hidden",
    max_retries=2,
)

from tools import web_search, news_search, wikipedia_lookup, read_url, arxiv_search


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
    - **Do not call any tool more than twice.**

    FACT-CHECKING & CLAIM VERIFICATION RULES:
    - Detect factual statements, statistics, or claims in the passage.  
    - Verify them using the most relevant tool:  
    • web_search → general info, broad claims.  
    • news_search → recent news/events.  
    • wikipedia_lookup → encyclopedic background.  
    • arxiv_search → research/academic claims.  
    - Use read_url to gather complete information when snippets are insufficient.    

    OUTPUT REQUIREMENTS:
    - Provide a short, clear, and accurate summary of the passage.  
    - Translate or summarize in English if the original text is in another language.  
    - If data is present, present it in a clean table format.  
    - Explicitly state whether any claims in the passage are true, false, or misleading, citing evidence.  
    - Keep the response factual, precise, and to the point.  
    - Do not hallucinate. Only rely on tool results for factual verification.  
    '''
)


PROMPT = textwrap.dedent(
    '''
    If the given text is long, provide a short, clear, and accurate summary of the passage.  
    Translate or summarize in English if the original text is in another language.
    If the text corresponds to some news or fact, state whether it is true, false, or misleading, citing evidence.
    Keep the response factual, precise, and to the point. Response should not be more that 4-5 sentences.
    You response should only have final summary, analysis, facts, etc. No need of detailed explanations and steps in the final response. 
    Do not hallucinate. Only rely on tool results for factual verification.
    ** Do all verification and analysis before, and then give user just the final summary of the text. **
    ** Do not use more than 5 tool calls (in total) **
    ** KEEP YOUR WHOLE FINAL RESPONSE UNDER 5 SENTENCES !!! **
    Text: {text}
    Summary and detailed analysis:
    '''
)

agent = create_react_agent(llm, tools=[web_search, news_search, read_url, wikipedia_lookup, arxiv_search], prompt=SYSTEM_PROMPT)

def invoke_agent(web_content: str):
    global agent
    events = agent.stream({"messages": [HumanMessage(content=PROMPT.format(text=web_content))]}, {"recursion_limit": 51})

    final_answer = None
    for event in events:
        if "agent" in event:
            agent_msg = event["agent"]
            if "messages" in agent_msg:

                msg = agent_msg["messages"][-1]
                if isinstance(msg, AIMessage):
                    final_answer = msg.content
    return final_answer

if __name__ == "__main__":
    web_content = "In the 2014 Indian general election, Modi led the BJP to a parliamentary majority, the first for a party since 1984."
    print(invoke_agent(web_content))

