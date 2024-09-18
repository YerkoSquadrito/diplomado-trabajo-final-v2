import pandas as pd
import os
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import dotenv
from langchain_openai import ChatOpenAI
from langchain.output_parsers.openai_tools import PydanticToolsParser
from langchain.schema.runnable import RunnableLambda
from langchain_core.pydantic_v1 import BaseModel, Field
import time
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain

from typing import Literal, TypedDict

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
#from langgraph.checkpoint import MemorySaver
#from langgraph.graph import END, StateGraph, MessagesState
#from langgraph.prebuilt import ToolNode, create_react_agent
from langchain_core.tools import tool
from pprint import pprint
#from langchain_experimental.utilities import PythonREPL
import json
import requests

from langchain_core.prompts import PromptTemplate
from typing import Literal, TypedDict
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, create_react_agent
from langchain_core.tools import tool
from pprint import pprint
import json
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.messages import HumanMessage, SystemMessage
#from langchain_experimental.utilities import PythonREPL
import operator


pathcsv = "./medicamentos/DrugData.csv"
dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
LANGCHAIN_API_KEY= os.environ["LANGCHAIN_API_KEY"]

#filtrar csv
def filtrar_csv(bd,column_name,colum_value):    
    df = pd.read_csv(bd)
    rows = df.loc[df[column_name].str.upper()== colum_value.upper()]    

    # Iterar sobre las filas de forma dinámica
    strrows=""
    for index, row in rows.iterrows():
        #print(f"Fila {index}:")
        for col_name in df.columns:  # Iterar sobre el nombre dinámico de las columnas
            strrows+=  f"{col_name}: {row[col_name]},"
        strrows+="\n"
    return (strrows)

#info_medicamentos = filtrar_csv(pathcsv,'Drug Name', 'Omeprazole')
#print(info_medicamentos)



#Mejora Redacción de la consulta
def LLM_MejorarConsulta(question:str):

    # Integrar el prompt en una cadena
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)

    # Crear una plantilla de prompt
    prompt_template = PromptTemplate(
        template="""Tu función es analizar si la pregunta de un usuario cumple ciertas reglas dadas y responder según cada regla.
        
        #reglas:    
        1- analizar si la pregunta indica explicitamente  algún medicamento. Si no es así. Debes solicitar que indique un medicamento en su pregunta
        2- si la pregunta pide que le recomiendes algún medicamento para un malestar o similar, debes responder que no puedes recomendar medicamento, que consulte a un médico
        3- si la pregunta cumple con lo anterior debes mejorar la redacción de la consulta y responder sólo con la pregunta mejorada.
        

        \nPregunta: '''{question}''' 

        """,
        input_variables=['question']
    )

    # Ejecutar la cadena con un contexto y una pregunta específicos

    chain = prompt_template | llm
    response = chain.invoke({'question': question})
    return(response.content)


#Grafo

@tool

def filtrar_medicamentos(
    nombre_medicamento: Annotated[str, "el nombre del medicamento a buscar información"],) -> str:
        """Busca información de medicamentos en una base de datos específica de medicamentos"""
        print("filtrar_medicamentos:",nombre_medicamento)        
        info_medicamentos = filtrar_csv(pathcsv,'Drug Name', nombre_medicamento)

        return info_medicamentos


tools = [filtrar_medicamentos]

# Inicializa el modelo
model = ChatOpenAI(model="gpt-4o", temperature=0).bind_tools(tools)


# Define la función que determina si continuar o no
def should_continue(state: dict) -> Literal["tools", END]:
    messages = state['messages']
    last_message = messages[-1]
    # Si el LLM hace una llamada a una herramienta, entonces nos dirigimos al nodo "tools"
    if last_message.tool_calls:
        return "tools"
    # Si el LLM incluyó el texto FINAL ANSWER, es porque terminó con su misión
    if "FINAL ANSWER" in last_message.content:
        # Any agent decided the work is done
        return "__end__"
    # Si no, entonces seguimos
    return "__end__"

# Define la función que llama al modelo
def main_agent(state: dict):
    messages = state['messages']
    response = model.invoke(messages)
    
    #print("messages:", messages)
    #print("Respuesta del modelo:")
    #print(response)
    # Devolvemos una lista, porque esto se añadirá a la lista existente
    return {"messages": [response]}

# Defino el objeto State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# Define un nuevo grafo
workflow = StateGraph(AgentState)

# Define los dos nodos entre los que vamos a alternar
workflow.add_node("agent", main_agent)
workflow.add_node("tool_node", ToolNode(tools))

# Establece el punto de entrada como `agent`
# Esto significa que este nodo es el primero en ser llamado
workflow.set_entry_point("agent")

# Ahora añadimos un borde condicional
workflow.add_conditional_edges(
    # Primero, definimos el nodo de inicio. Usamos `agent`.
    # Esto significa que estos son los bordes que se toman después de que se llama al nodo `agent`.
    "agent",
    # Luego, pasamos la función que determinará qué nodo se llama a continuación.
    should_continue,
    {"tools": "tool_node", "__end__": END},

)

# Ahora añadimos un edge normal de `tools` a `agent`.
# Esto significa que después de que se llama a `tools`, el nodo `agent` se llama a continuación.
workflow.add_edge("tool_node", 'agent')

# Inicializa la memoria para persistir el estado entre ejecuciones del grafo
checkpointer = MemorySaver()

# Finalmente, ¡lo compilamos!
# Esto lo compila en un LangChain Runnable,
# lo que significa que puedes usarlo como usarías cualquier otro runnable.
# Ten en cuenta que estamos (opcionalmente) pasando la memoria al compilar el grafo
app = workflow.compile(checkpointer=checkpointer)


# dibujamos el grafo
#from IPython.display import Image, display
#display(Image(app.get_graph(xray=True).draw_mermaid_png()))


# Define la consulta inicial y el mensaje del sistema
system_message = """Debes responder preguntas sobre medicamentos utilizando exclusivamente la información proporcionada en el listado o base de datos de medicamentos que se te ha entregado. No debes ofrecer información adicional ni hacer suposiciones fuera de los datos dados. Si no encuentras la respuesta a una pregunta dentro de la información proporcionada, debes indicarlo explícitamente al usuario.
La información que conoces es:  'Drug Name', 'Generic Name', 'Drug Class', 'Indications', 'Dosage Form', 'Strength', 'Route of Administration', 'Mechanism of Action', 'Side Effects', 'Contraindications', 'Interactions', 'Warnings and Precautions', 'Pregnancy Category', 'Storage Conditions', 'Manufacturer', 'Approval Date', 'Availability', 'NDC', 'Price'.
Debes utilizar una tool con el nombre del medicamento en inglés para buscar información exactamente del medicamento que se te pregunta.
Debes rescatar el nombre del medicamento de la pregunta del usuario y llamar a la tool. En caso que el usuario no indique el nombre de usuario, debes responder solicitandóselo.

#instrucciones
- Cuando tengas una respuesta final, comienza tu mensaje con el texto FINAL RESPONSE. Responde siempre en Español.
- Si no encuentras información del medicamento debes responder que no tienes información. No debes agregar información de conocimiento general adicional.
- Si se te pregunta por otra información que desconoces, puedes sugerir las columnas que tienes información.


"""


###Módulo principal
def main_drug_specialist(question):
    questionopt = LLM_MejorarConsulta(question)
    print("pregunta original :", question)
    print("pregunta mejorada :", questionopt)
    
    #eejcutar question
    result = app.invoke(
    {"messages":
        [SystemMessage(content=system_message),
        HumanMessage(content=questionopt)]
    },
    
    config={"configurable": {"thread_id": 2}}
    )
    response = result["messages"][-1].content
    response = response.replace("FINAL RESPONSE:","").replace("FINAL RESPONSE","")
    return(response)

def main_drug_specialist_with_history(input):    
    question =  input["messages"][-1].content
    questionopt = LLM_MejorarConsulta(question)
    print("pregunta original :", question)
    print("pregunta mejorada :", questionopt)
    
    messages = {"messages": input["messages"] + [SystemMessage(content=system_message), HumanMessage(content=questionopt)]}

    #eejcutar question
    result = app.invoke(
        messages,    
        config={"configurable": {"thread_id": 2}}
    )
    response = result["messages"][-1].content
    response = response.replace("FINAL RESPONSE:","").replace("FINAL RESPONSE","")
    return(response)

def main_drug_specialist_test(question): 
    questionopt = LLM_MejorarConsulta(question)
    print("pregunta original :", question)
    print("pregunta mejorada :", questionopt)

    for event in app.stream(
        {"messages":
        [SystemMessage(content=system_message),
        HumanMessage(content=questionopt)]},
        config={"configurable": {"thread_id": 1}}
    ):
        for k, v in event.items():
            if k != "__end__":
                print(v)
    
    return "FIN RESPONSE"