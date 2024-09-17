from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from .global_llm_instances import global_llm
from langchain_core.runnables import Runnable
import os

# IMPORTANT: Modify as needed for your use case. In this case, we are routing to 3 possible destinations.
class RouteQuery(BaseModel):
    """Route a user query to the most relevant datasource."""
    datasource: Literal["vectorstore", "out_of_scope"] = Field( # web_search is not included here, but could be added if needed and later powered by Tavily.
        ...,
        description="Given a user question choose to route it to a vectorstore or mark it as out of scope.", # web_search is not included here, but could be added if needed and later powered by Tavily.
    )

# IMPORTANT: Modify as needed for your use case. In this case, we are routing to 3 possible destinations, which are described below.
system_prompt = """You are an expert at routing a user question to a vectorstore or marking them as out of scope.
The vectorstore contains documents related to Accenture's internal portal, 
benefits for employees and other general enterprise directions.
Use the vectorstore for questions on these topics.
If the question is out of scope, mark it as such."""

# EXAMPLE for when using web search as a destination. Every new option must be added to the RouteQuery class and the system_prompt.
system_prompt_with_web_search = """You are an expert at routing a user question to a vectorstore, web search or marking them as out of scope.
The vectorstore contains documents related to Accenture's internal portal, 
benefits for employees and other general enterprise directions.
Use the vectorstore for questions on these topics. Use web-search for other general information about Accenture.
If the question is out of scope, mark it as such."""

# Prompt
route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{question}"),
    ]
)

def build_router_chain(
        llm = global_llm,
        output_schema = RouteQuery,
        prompt = route_prompt
    ) -> Runnable:
    """
    Builds a router chain for routing user questions to a vectorstore or web search.

    Chain input can be string or a dictionary with:
    - question: The user question.
    
    Inputs:
        llm (ChatOpenAI): The language model to use. Defaults to gpt-4o-mini.
        output_schema (BaseModel): The structured output schema for the router. Defaults to routing schema for Accenture's internal chatbot chatbot use case.
        system_prompt (str): The system prompt for the router. Defaults to routing for Accenture's internal chatbot use case.
    
    Returns:
        question_router (ChatRouter): The router chain for routing user questions.
    """
    # LLM with function call
    structured_llm_router = llm.with_structured_output(output_schema)

    question_router = prompt | structured_llm_router

    return question_router
