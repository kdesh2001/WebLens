import os
from getpass import getpass
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
import textwrap
from dotenv import load_dotenv
load_dotenv()

os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HUGGINGFACEHUB_API_TOKEN") or getpass("HF token: ")

@tool
def spl_func(n: int) -> int:
    """Special function tool. Takes int input, returns a value after applying the function"""
    return (2*n+1)**3

hf_llm = HuggingFaceEndpoint(
    repo_id="openai/gpt-oss-20b",
    task="text-generation",
    
    huggingfacehub_api_token=os.environ["HUGGINGFACEHUB_API_TOKEN"],
    max_new_tokens=256,
    temperature=0.3,
)

chat_llm = ChatHuggingFace(llm=hf_llm)

PROMPT = textwrap.dedent(
    """
    You are an expert at text summarization. Read the following text carefully and produce a summary in no more than 2-3 sentences. Your summary must:

    Capture the most crucial details and key information from the text.

    Be a highly accurate and faithful representation of the original content without distortion or omission of critical facts.

    Avoid unnecessary details, repetition, or subjective interpretation.

    If the content is in any other language, translate it into English (return full translated content as it is for short text, for long text summarise it in English.)

    If (and only if) the text contains any data, statistics or any information that can be represented well in a table, analyse the data and put it into a table like structure in your response.

    Be concise, clear, and to the point.

    Text: {text}
    Summary:
    """
)

agent = create_react_agent(chat_llm, tools=[spl_func])

def invoke_agent(web_content: str):
    conv = agent.invoke({"messages": [HumanMessage(content=PROMPT.format(text=web_content))]})
    assistant_response = (conv["messages"][-1].content).split("assistantfinal")[-1]
    return assistant_response

if __name__ == "__main__":
    web_content = "Languid and easy on the eye, Rohit Sharma owned all the shots in the book when he emerged from the Mumbai suburbs as heir apparent to the Indian batting greats of the 2000s. It took him time and persistence, but by the 2010s he had become a colossus in white-ball cricket, and the man in charge of perhaps the most formidable league team in the first age of T20. That Rohit had talent was apparent to both the casual observer and to the trained eye. Fans were frustrated at the long wait for the potential to translate into runs, though selectors and captains, knowing better, kept backing him. At one point the word 'talent' was Rohit's bugbear, a pejorative nickname for him on social media. Once it all clicked, though - the move to open the batting in ODIs late in 2012 was one particular turning point - things came together spectacularly."
    conv = agent.invoke({"messages": [HumanMessage(content=PROMPT.format(text=web_content))]})
    assistant_response = (conv["messages"][-1].content).split("assistantfinal")[-1]
    print(assistant_response)
