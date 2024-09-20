from medicamentos.drugspecialist import main_drug_specialist, main_drug_specialist_with_history
from chain_builders.question_router import build_router_chain
from chain_builders.standard_chat_chain import build_standard_chat_chain
from typing import Literal, Optional
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Annotated, TypedDict, List
import operator
from langchain_core.messages import BaseMessage, AIMessage, filter_messages, HumanMessage
from langgraph.graph import END, StateGraph, START
from modulo_farmacia import respond_farmacia

# AGENTS
## FIRST ROUTER
class RouteQuery(BaseModel):
    """Route a user query to the most relevant destination."""
    datasource: Literal["in_scope", "out_of_scope"] = Field( 
        ...,
        description="Given a user question choose to classify it as in_scope or out_of_scope.",
    )
system_prompt = """You are an expert at routing a user question to different AI agents.
Consider a question *within scope* if it is related to the capabilities of the AI agents available.
- Drug specialist: Knows about drugs and their effects. Use this ONLY if the question is about an specific drug explicitly. If the user is asking for a drug recommendation DO NOT use this agent.
- Pharmacy store: Knows about the store, its location, opening hours, and other general information.

Consider a question *out of scope* if:
- It is not related to the capabilities of the AI agents available
- It asks explicitly for a drug recommendation. IMPORTANT: In this case, you should NOT use the drug specialist agent.
- It is a general request like "Summarize the conversation so far"
"""
route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder("chat_history")
    ]
)
first_question_router = build_router_chain(prompt=route_prompt, output_schema=RouteQuery)

## SECOND ROUTER
class RouteQuery(BaseModel):
    """Route a user query to the most relevant destination."""
    datasource: Literal["drug_specialist", "pharmacy_store_specialist","out_of_scope"] = Field( 
        ...,
        description="Given a user question choose to where to route it between a drug_specialist, a pharmacy_store_specialist or out_of_scope.",
    )
system_prompt = """You are an expert at routing a user question to different AI agents.
The posible destinations are:
- Drug specialist: Knows about drugs and their effects. Use this ONLY if the question is about an specific drug explicitly. If the user is asking for a drug recommendation DO NOT use this agent.
- Pharmacy store specialist: Knows about the store, its location, opening hours, and other general information.
- Out of scope: If the question is not related to the capabilities of the AI agents available, or if it asks explicitly for a drug recommendation. IMPORTANT: In this case, you should NOT use the drug specialist agent.
"""
route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder("chat_history")
    ]
)
second_question_router = build_router_chain(prompt=route_prompt, output_schema=RouteQuery)

## 2) Helpful Assistant
system_prompt = """# GENERAL INSTRUCTIONS:
- You are a helpful AI assistant developed by GROUP 2, made for answering questions about specific pharmaceautical drugs and pharmacy stores in Chile.
- EXTREMELY IMPORTANT: You should NOT give any drug recommendations to the user. If the user asks for ANY medical recommendation, you MUST recommend to ask a doctor.
- Generate an answer to the user question. Be friendly, expresive and not so formal.
- You can also answer general requests like "Summarize the conversation so far"
- If the question has nothing to do with your expertise, don't respond and remind the user who you are and what your capabilities are.
- If you don't know the answer, just say you don't know and ask the user for more information.

# OTHER INSTRUCTIONS:
- ALWAYS respond in the language the user is asking.
"""
generalist_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder("chat_history")
    ]
)
generalist_assistant = build_standard_chat_chain(prompt=generalist_prompt)


# Graph state
class State(TypedDict):
    chat_history: Annotated[List[BaseMessage], operator.add]
    designated_agent: Optional[str]

# Graph nodes definition
def first_question_router_node(state):
    chat_history = state["chat_history"]
    source = first_question_router.invoke({"chat_history": chat_history})
    return {"designated_agent": source.datasource}

def second_question_router_node(state):
    chat_history = state["chat_history"]
    source = second_question_router.invoke({"chat_history": chat_history})
    return {"designated_agent": source.datasource}

def generalist_assistant_node(state):
    chat_history = state["chat_history"]
    response =  generalist_assistant.invoke({"chat_history": chat_history})
    return {"chat_history": [AIMessage(content=response, name='generalist')]}

def pharmacy_store_specialist(state):
    chat_history = state["chat_history"]
    input = {
        "chat_history": chat_history,
    }
    specialist_json_response = respond_farmacia(input)
    # output = active_rag_graph.invoke(input)
    return {"chat_history": [AIMessage(content=specialist_json_response['generation'], name="pharmacy_store_specialist")]}

def drug_specialist(state):
    chat_history = state["chat_history"]
    input = {
        "messages": chat_history,
    }

    question = (input["messages"][-1].content)
    response = main_drug_specialist_with_history(input)

    output = {"generation": response}    
    return {"chat_history": [AIMessage(content=output['generation'], name="drug_specialist")]}


# Graph Edges definition
def first_question_router_edges(state):
    """
    Route question to the designated agent.

    Args:
        state (dict): The current graph state

    Returns:
        str: Next node to call
    """
    designated_agent = state["designated_agent"]
    if designated_agent == "in_scope":
        return "second_question_router"
    elif designated_agent == "out_of_scope":
        return "generalist"
    
def second_question_router_edges(state):
    """
    Route question to the designated agent.

    Args:
        state (dict): The current graph state

    Returns:
        str: Next node to call
    """
    designated_agent = state["designated_agent"]
    if designated_agent == "out_of_scope":
        return "generalist"
    elif designated_agent == "drug_specialist":
        return "drug_specialist"
    elif designated_agent == "pharmacy_store_specialist":
        return "pharmacy_store_specialist"

# Define the graph.
chatbot = StateGraph(State)
# # Nodes
chatbot.add_node("first_question_router", first_question_router_node)
chatbot.add_node("second_question_router", second_question_router_node)
chatbot.add_node("generalist", generalist_assistant_node)
chatbot.add_node("pharmacy_store_specialist", pharmacy_store_specialist)
chatbot.add_node("drug_specialist", drug_specialist)
# # Edges
chatbot.add_edge(START, "first_question_router")
chatbot.add_edge("generalist", END)
chatbot.add_edge("pharmacy_store_specialist", END)
chatbot.add_edge("drug_specialist", END)
chatbot.add_conditional_edges(
    "first_question_router",
    first_question_router_edges,
    {
        "second_question_router": "second_question_router",
        "generalist": "generalist",
    }
)
chatbot.add_conditional_edges(
    "second_question_router",
    second_question_router_edges,
    {
        "generalist": "generalist",
        "pharmacy_store_specialist": "pharmacy_store_specialist",
        "drug_specialist": "drug_specialist"
    }
)

chatbot = chatbot.compile()
