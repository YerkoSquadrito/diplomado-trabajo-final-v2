import json
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
# Agrega la carpeta raíz al sys.path
# import sys
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from conf.config import URL_FARMACIAS, URL_FARMACIAS_TURNO
from conf.funciones import get_farmacias, imprime_Excel, generar_metadatos, prompt_pandas, prompt_respuesta, get_respuesta_final
import pandas as pd
from pprint import pprint
from tabulate import tabulate
from langchain_core.pydantic_v1 import BaseModel, Field

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")

os.environ["LANGCHAIN_API_KEY"] = langchain_api_key
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "TRABAJO-FARMACIAS"

   
# Definir la clase Pydantic 'respuesta'
class Pyd_respuesta(BaseModel):
    codigo_resp: bool = Field(description="Código de respuesta OK o NOK")
    detalle_resp: str = Field(description="Respuesta a la pregunta. Código pandas para realizar la búsqueda")

def main(input_data):
    # Asegurarse de que chat_history esté disponible y correctamente inicializado
    chat_history = input_data.get("chat_history", [])
    #Obtiene las farmacias en formato pandas.DataFrame
    pd_farmacias = get_farmacias()
    # pprint(pd_farmacias.head())
    
    #Escribe el DataFrame en un archivo Excel
    imprime_Excel(pd_farmacias, "farmacias.xlsx")


    # Leer el último mensaje del chat_history
    last_message = input_data["chat_history"][-1]  # Obtiene el último mensaje de la lista
    user_question = last_message["content"] 

    print(f"Último mensaje recibido: {user_question}")

    metadatos_farmacias = generar_metadatos(pd_farmacias)

# -------------------------
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    parser = JsonOutputParser(pydantic_object=Pyd_respuesta)

    llm_respuesta = ChatOpenAI(model="gpt-4o", temperature=0.7)


    response_prompt_template = prompt_pandas()
    response_prompt_respuesta = prompt_respuesta()


    # Crear el prompt parcial
    partial_prompt = response_prompt_template.partial(
        format_instructions=parser.get_format_instructions()
    )
    chain = partial_prompt | llm | parser
    
    response = chain.invoke({"metadata":metadatos_farmacias, "user_question":user_question}) 
    print(response)

    #definir resultado como un dataframe pandas
    pd_resultado = pd.DataFrame()

    #define objeto output
    output = {}

    #Solo ejecuta cuando el código de respuesta es OK
    if response["codigo_resp"] == "OK":
        pd_resultado = eval(response["detalle_resp"])


    if response["codigo_resp"] == "OK" and not pd_resultado.empty:
        

        print("El resultado del filtro es:")
        print(pd_resultado)

        imprime_Excel(pd_resultado, "resLLM.xlsx")

        # Formatear los datos en un texto descriptivo
        farmacias_encontradas = []
        for _, row in pd_resultado.iterrows():
            farmacia_info = (
            f"Farmacia: {row['local_nombre']} - Dirección: {row['local_direccion']} - "
            f"Teléfono: {row['local_telefono']} - Horario: {row['funcionamiento_hora_apertura']} a {row['funcionamiento_hora_cierre']} - "
            f"En turno: {'Sí' if row['en_turno'] == 1 else 'No'} - Origen: {row['origen']}"
                            )
            farmacias_encontradas.append(farmacia_info)

        # Unir las descripciones en un solo texto
        texto_resumen = "\n".join(farmacias_encontradas)
        print("Texto resumen:", texto_resumen)

        chain_usuario = response_prompt_respuesta | llm_respuesta| StrOutputParser()

        response_usuario = chain_usuario.invoke({"farmacias_encontradas":texto_resumen, "user_question":user_question})

        print("Respuesta al usuario:", response_usuario)

        # ----Genera respuesta final-------

        #Obtiene chat_history
        chat_history = input_data["chat_history"]
        # pprint (f"Chat_history 1 : {chat_history}")


        #Agrega respuesta del LLM a chat_history
        chat_history.append({"role": "system", "content":response_usuario})
        # pprint (f"Chat_history 2 : {chat_history}")


    elif response["codigo_resp"] == "OK" and pd_resultado.empty:
        # Mostrar el mensaje sin ejecutar
        print("Respuesta OK pero no se encontraron resultados en DATAFRAME.")
        print("Mensaje:", response["detalle_resp"])
        chat_history.append({"role": "system", "content":"No se encontraron resultados."})


    elif response["codigo_resp"] == "NOK":
        # Mostrar el mensaje sin ejecutar
        print("No se encontraron resultados.")
        print("Mensaje:", response["detalle_resp"])
        chat_history.append({"role": "system", "content":response["detalle_resp"]})
    

    # Crear el objeto output
    output = {
            "chat_history": chat_history,
            "query_sql": response["detalle_resp"],
            "output_sql": pd_resultado.to_string(index=False)
            }


    #Imprime objeto a devolver.
    print("**********\n")
    # pprint (f"OBJETO OUTPUT  : \n {output}")
    #Imprimir objeto output de forma ordenada
    print(json.dumps(output, indent=4))
    # return output

if __name__ == '__main__':

    # Input que se recibiría de otra aplicación
    input_data = {
        "chat_history": [
            {"role": "system", "content": "Hola, soy tu asistente de farmacias."},
            # {"role": "user", "content": "¿Cuáles son las farmacias CRUZ VERDE DE TURNO ABIERTAS A LAS 20:00 HORAS?"}
            {"role": "user", "content": "¿Cuáles son las farmacias de turno en Macul?"}

        ]
    }
    main(input_data)

