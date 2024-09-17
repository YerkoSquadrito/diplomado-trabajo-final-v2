from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from conf.config import URL_FARMACIAS, URL_FARMACIAS_TURNO
from conf.funciones import get_farmacias, generar_metadatos, prompt_pandas, prompt_respuesta
import pandas as pd
from langchain_core.pydantic_v1 import BaseModel, Field

load_dotenv()
   
class Pyd_respuesta(BaseModel):
    codigo_resp: bool = Field(description="Código de respuesta OK o NOK")
    detalle_resp: str = Field(description="Respuesta a la pregunta. Código pandas para realizar la búsqueda")

def respond_farmacia(input_data):
    pd_farmacias = get_farmacias()
    
    last_message = input_data["chat_history"][-1]
    user_question = last_message.content

    metadatos_farmacias = generar_metadatos(pd_farmacias)
    
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

    #definir resultado como un dataframe pandas
    pd_resultado = pd.DataFrame()

    #Solo ejecuta cuando el código de respuesta es OK
    if response["codigo_resp"] == "OK":
        pd_resultado = eval(response["detalle_resp"])


    if response["codigo_resp"] == "OK" and not pd_resultado.empty:
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
        chain_usuario = response_prompt_respuesta | llm_respuesta| StrOutputParser()
        ai_message = chain_usuario.invoke({"farmacias_encontradas":texto_resumen, "user_question":user_question})
    
    elif response["codigo_resp"] == "OK" and pd_resultado.empty:
        ai_message = "No se encontraron resultados."
    
    elif response["codigo_resp"] == "NOK":
        ai_message = response["detalle_resp"]
   
    else:
        ai_message = "Creo que hubo un problema. Vuelve a intentarlo"
    
    output = {
            "generation": ai_message,
            "query_sql": response["detalle_resp"],
            "output_sql": pd_resultado.to_string(index=False)
            }
    return output

