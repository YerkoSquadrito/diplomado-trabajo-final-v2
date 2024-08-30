from chain_builders.question_router import build_router_chain
from chain_builders.standard_chat_chain import build_standard_chat_chain
from typing import Literal
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Annotated, TypedDict, List
import operator
from langchain_core.messages import BaseMessage, AIMessage, filter_messages, HumanMessage
from langgraph.graph import END, StateGraph, START

# AGENTS
## 1) Router
class RouteQuery(BaseModel):
    """Route a user query to the most relevant destination."""
    datasource: Literal["benefits_and_learning", "generalist"] = Field( 
        ...,
        description="Given a user question choose to route it to an Accenture's benefits & learning specialist agent or to a generalist agent",
    )
system_prompt = """You are an expert at routing a user question to different AI agents: an Accenture's benefits & learning specialist agent and a generalist agent.
The specialist knows about Accenture's internal portal, learning options, benefits for employees and other general enterprise directions.
Use the specialist if you need more information on these topics to respond. 
Use the generalist for other topics and for requests like 'rewrite your last answer in another manner'."""
route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder("chat_history")
    ]
)
question_router = build_router_chain(prompt=route_prompt, output_schema=RouteQuery)

## 2) Helpful Assistant
system_prompt = """# GENERAL INSTRUCTIONS:
- You are a helpful AI assistant developed by Accenture Chile Gen AI practice, made for Accenture Chile employees.
- Your area of expertise is Accenture Chile benefits and learning oportunities. 
- Generate an answer to the user question. Be friendly, expresive and not so formal. 
- If the question has nothing to do with Accenture or work in general, don't respond and remind the user who you are and your capabilities.
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
    messages: Annotated[List[BaseMessage], operator.add]
    designated_agent: str

# Graph nodes definition
def benefits_and_learning_node(state):
    chat_history = state["messages"]
    input = {
        "chat_history": chat_history,
        "loop_prevention": 0,
        "verbose": False
    }
    active_rag_output = active_rag_graph.invoke(input)
    return {"messages": [AIMessage(content=active_rag_output['generation'], name="Benefits_and_Learning_Specialist")]}


def generalist_assistant_node(state):
    chat_history = state["messages"]
    response =  generalist_assistant.invoke({"chat_history": chat_history})
    return {"messages": [AIMessage(content=response, name='Generalist')]}

def router_node(state):
    chat_history = state["messages"]
    source = question_router.invoke({"chat_history": chat_history})
    return {"designated_agent": source.datasource}


# Graph Edges definition
def route_question(state):
    """
    Route question to RAG or out_of_scope.

    Args:
        state (dict): The current graph state

    Returns:
        str: Next node to call
    """
    designated_agent = state["designated_agent"]
    if designated_agent == "benefits_and_learning":
        return "benefits_and_learning"
    elif designated_agent == "generalist":
        return "generalist"


# Define the graph.
chatbot = StateGraph(State)
# # Nodes
# chatbot.add_node("router", router_node)
# chatbot.add_node("benefits_and_learning", benefits_and_learning_node)
# chatbot.add_node("generalist", generalist_assistant_node)
# # Edges
# chatbot.add_edge(START, "router")
chatbot.add_edge(START, "generalist")
# chatbot.add_edge("generalist", END)
# chatbot.add_edge("benefits_and_learning", END)
# chatbot.add_conditional_edges(
#     "router",
#     route_question,
#     {
#         "benefits_and_learning": "benefits_and_learning",
#         "generalist": "generalist",
#     },
# )

chatbot = chatbot.compile()
