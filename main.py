from typing import List

from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.messages import HumanMessage
# from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch

#Pydantic objects which will make the required format for output for json
class Source(BaseModel):
    """Schema for a source used by the agent"""

    url: str = Field(description="The URL of the source")

#Pydantic objects which will make the required format for output for json
class AgentResponse(BaseModel):
    """Schema for agent response with answer and sources"""

    answer: str = Field(description="Thr agent's answer to the query")
    sources: List[Source] = Field(
        default_factory=list, description="List of sources used to generate the answer"
    )


# llm = ChatOpenAI(model="gpt-5")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
tools = [TavilySearch()]
agent = create_agent(model=llm, tools=tools, response_format=AgentResponse)


def main():
    print("Hello from langchain-course!")
    result = agent.invoke(
        {
            "messages": HumanMessage(
                content="search for 3 job postings for an ai engineer using langchain in Hyderabad on linkedin and list their details?"
            )
        }
    )
    print(result["structured_response"])


if __name__ == "__main__":
    main()
