
import os
from getpass import getpass
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
import textwrap
from dotenv import load_dotenv
load_dotenv()


os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HUGGINGFACEHUB_API_TOKEN") or getpass("HF token: ")

@tool
def spl_func(n: int) -> int:
    """Special function tool. Takes int input, returns a value after applying the speacial function"""
    return (n+1)**3

@tool
def normal_func(n: int) -> int:
    """Normal function tool. Takes int input, returns a value after applying the normal function"""
    return 3*n

hf_llm = HuggingFaceEndpoint(
    repo_id="openai/gpt-oss-20b",
    task="text-generation",
    
    huggingfacehub_api_token=os.environ["HUGGINGFACEHUB_API_TOKEN"],
    max_new_tokens=1024,
    temperature=0.1,
    cache=False
)

chat_llm = ChatHuggingFace(llm=hf_llm)

SYSTEM_PROMPT = "You are a helpful assistant. You have access to following tools - spl_func and normal_func - Use them when needed."

agent = create_react_agent(chat_llm, tools=[spl_func, normal_func], prompt=SYSTEM_PROMPT)

def invoke_agent(web_content: str):
    global agent
    events = agent.stream({"messages": [HumanMessage(content=web_content)]})
    final_answer = []
    for event in events:
        final_answer.append(event)
    assistant_response = final_answer
    return assistant_response

if __name__ == "__main__":
    web_content = "What is the value of spl_func(normal_func(7)) ?"
    
    ai_messages = invoke_agent(web_content)
    for msg in ai_messages:
        print(msg)
        print("***************")
    ''''
    analysisThe user: "What is the value of spl_func(4) and spl_func(6) ? Call the given spl_func() tool". The tool might return some function value. We need to call two times. We should produce two calls. Provide the values? The tool likely returns something like 343 for 4. Let's call for 6. We'll call again.assistantcommentary to=functions.spl_funcjson{"n":6}
    '''
