import requests  # Para hacer peticiones HTTP
import openpyxl
import os
import pandas as pd
import json
from pathlib import Path
from conf.config import URL_FARMACIAS, URL_FARMACIAS_TURNO
from langchain_core.prompts import ChatPromptTemplate


def get_farmacias():
    '''Obtiene farmacias desde URL_FARMACIAS y URL_FARMACIAS_TURNO y unifica ambos DataFrames 
    en uno solo, priorizando farmacias_turno y agregando las columnas 'origen' y 'en_turno'.'''

    # Obtener los datos de las URLs
    response_farmacias = requests.get(URL_FARMACIAS)
    response_farmacias_turno = requests.get(URL_FARMACIAS_TURNO)

    # Convertir el JSON a objetos pandas DataFrame
    farmacias = pd.DataFrame(response_farmacias.json())
    farmacias_turno = pd.DataFrame(response_farmacias_turno.json())

    # Agregar la columna 'origen' y 'en_turno' a cada DataFrame
    farmacias['origen'] = 'general'
    farmacias['en_turno'] = 0

    farmacias_turno['origen'] = 'turno'
    farmacias_turno['en_turno'] = 1

    # Unificar ambos DataFrames, priorizando farmacias_turno en caso de duplicados
    farmacias_unidas = pd.concat([farmacias_turno, farmacias]).drop_duplicates(subset='local_id', keep='first')

    return farmacias_unidas

def imprime_Excel(pd_farmacias,nombrearchivo):
    '''Escribe el DataFrame pd_farmacias en un archivo Excel
    Input:  pd_farmaciaas: DataFrame de pandas
            nombrearchivo: nombre del archivo Excel
    '''

    # Crear un archivo Excel
    pd_farmacias.to_excel(nombrearchivo, index=False)

    print(f"{nombrearchivo} creado con éxito.")

def generar_metadatos(dataframe):

    '''Genera metadatos detallados para cada columna del DataFrame basándose en el nombre de la columna.'''
    
    metadatos = {}
    
    for column in dataframe.columns:
        # Inicializamos un diccionario para cada columna
        columna_metadato = {
            "tipo_de_dato": str(dataframe[column].dtype),
            "descripcion": "",
            # "valores_unicos": dataframe[column].unique().tolist() if dataframe[column].nunique() < 10 else "Muchos valores únicos"
        }
        
        # Detalles específicos según el nombre de la columna
        if "fecha" in column:
            columna_metadato["descripcion"] = "Fecha en la que se recopiló la información o se realizó la consulta."
        
        elif "local_id" in column:
            columna_metadato["descripcion"] = "Identificador único del local o farmacia."

        elif "local_nombre" in column:
            columna_metadato["descripcion"] = "Nombre de la farmacia o local."

        elif "comuna_nombre" in column:
            columna_metadato["descripcion"] = "Nombre de la comuna donde se encuentra la farmacia."

        elif "localidad_nombre" in column:
            columna_metadato["descripcion"] = "Nombre de la localidad específica dentro de la comuna."

        elif "local_direccion" in column:
            columna_metadato["descripcion"] = "Dirección física de la farmacia o local."

        elif "funcionamiento_hora_apertura" in column:
            columna_metadato["descripcion"] = "Hora de apertura del local en el día indicado."

        elif "funcionamiento_hora_cierre" in column:
            columna_metadato["descripcion"] = "Hora de cierre del local en el día indicado."

        elif "local_telefono" in column:
            columna_metadato["descripcion"] = "Número de teléfono de contacto del local o farmacia."

        elif "local_lat" in column or "local_lng" in column:
            columna_metadato["descripcion"] = "Coordenadas geográficas del local o farmacia (latitud y longitud)."

        elif "funcionamiento_dia" in column:
            columna_metadato["descripcion"] = "Día de la semana para el que aplica el horario de funcionamiento."

        # elif "fk_region" in column:
        #     columna_metadato["descripcion"] = "Clave foránea que identifica la región en la que se encuentra la farmacia."

        # elif "fk_comuna" in column:
        #     columna_metadato["descripcion"] = "Clave foránea que identifica la comuna en la que se encuentra la farmacia."

        # elif "fk_localidad" in column:
        #     columna_metadato["descripcion"] = "Clave foránea que identifica la localidad específica dentro de la comuna."

        # elif "origen" in column:
        #     columna_metadato["descripcion"] = "Indica si el dato proviene de la lista general de farmacias o de farmacias de turno."

        elif "en_turno" in column:
            columna_metadato["descripcion"] = "Indica si la farmacia está en turno (1) o no (0) en la fecha indicada."

        else:
            columna_metadato["descripcion"] = "Descripción no especificada."

        # Añadir el metadato de la columna al diccionario de metadatos
        metadatos[column] = columna_metadato
    
    return metadatos

def prompt_pandas():

    response_prompt_template = ChatPromptTemplate.from_template("""
        **Instrucción: Eres un experto en análisis de datos y programación en Python con Pandas. Tienes un DataFrame que contiene información sobre farmacias en diferentes comunas y regiones de Chile. 
        **1. Restricción: Solo debes responder preguntas relacionadas con el ámbito de farmacias. 
        **2. Solo debes responder con información de farmacias de Chile y ningún otro país.
        **3. Ante una pregunta incorrecta, el formato de respuesta debería ser algo así:
            codigo_resp: "NOK"
            detalle_resp: Responder un mensaje de acuerdo al error.
        Aquí está la metadata del DataFrame que se llama "pd_farmacias", la respuesta la asignará a la variable "resultado":
        {metadata}
        La pregunta del usuario es la siguiente:
        {user_question}
        A continuación, te proporciono algunos ejemplos de preguntas y sus respuestas en forma de código:
        Ejemplo 1:
        Pregunta: "¿Cuáles son las farmacias de turno en la comuna de Providencia?"
        Respuesta esperada:
        codigo_resp: "OK"
        detalle_resp: pd_farmacias[(pd_farmacias['comuna_nombre'] == 'PROVIDENCIA') & (pd_farmacias['en_turno'] == 1)]
        Ejemplo 2:
        Pregunta: "¿Qué farmacias están en la región Metropolitana de Santiago?"
        Respuesta esperada:
        codigo_resp: "OK"
        detalle_resp: pd_farmacias[pd_farmacias['region'] == 'METROPOLITANA DE SANTIAGO']
        Ejemplo 3:
        Pregunta: "¿Cuáles son las farmacias abiertas después de las 20:00 en la comuna de ñuñoa?"
        Respuesta esperada:
        codigo_resp: "OK"
        detalle_resp: pd_farmacias[(pd_farmacias['comuna_nombre'] == 'ÑUÑOA') & (pd_farmacias['funcionamiento_hora_cierre'] > '20:00:00')]
        Ejemplo 4:
        Pregunta: "¿Cuáles serán las farmacias de turno mañana?"
        Respuesta esperada:
        codigo_resp: "NOK"
        detalle_resp: Solo puedo responder con información de hoy.
        Ejemplo 5:
        Pregunta: "¿Qué farmacias estuvieron de turno el 25 de agosto?"
        Respuesta esperada:
        codigo_resp: "NOK"
        detalle_resp: Solo puedo responder con información de hoy.
        Ejemplo 6:
        Pregunta: "¿Cuáles son las farmacias de turno en ARGENTINA?"
        Respuesta esperada:
        codigo_resp: "NOK"
        detalle_resp: Solo tengo conocimiento de farmacias de Chile.
        **Debes tener en cuenta lo siguiente:**
        - La variable "fecha" siempre tendrá el día actual.
        - Si la pregunta del usuario hace referencia a un día distinto al de hoy (por ejemplo, menciona "mañana", "ayer", o cualquier fecha específica), la pregunta es incorrecta y debes responder siempre de esta forma:
            codigo_resp: "NOK"
            detalle_resp: "Solo puedo responder con información de hoy."
        - No es necesario incluir la variable "fecha" en el comando pandas de la respuesta, ya que se entiende que siempre se consulta por el día actual.
        **Output**
        - *Con base en la pregunta del usuario, genera únicamente la línea de código Python que filtra el DataFrame para responder a la consulta.*
        - *El campo 'comuna_nombre' o 'region' debe ir siempre en mayúsculas y sin tildes en las vocales (pero conservando la letra 'Ñ') en el código Python de Pandas.*
        - *Al procesar los nombres de 'comuna_nombre' o 'region', reemplaza las vocales con tildes por su equivalente sin tilde (por ejemplo, 'Á' por 'A'), pero mantén la letra 'Ñ' sin cambios.*
        No incluyas ningún otro código adicional, solo la línea que realiza la búsqueda en el DataFrame. Si la pregunta es sobre un día diferente al de hoy, responde con: "Solo puedo responder con información de hoy."
        *Formato respuesta: {format_instructions}*
        - **codigo_resp**: Responde 'OK' cuando la pregunta es correcta. Responde 'NOK' cuando la pregunta es incorrecta.
        - **detalle_resp**: Línea de código Python que filtra el DataFrame para responder a la consulta cuando codigo_resp es 'OK'.
        """)
    return response_prompt_template


def prompt_respuesta():

    response_prompt_template = ChatPromptTemplate.from_template("""
Eres un asistente virtual experto en proporcionar información detallada sobre farmacias en Chile.

**Pregunta del Usuario:**
"{user_question}"

**Datos Encontrados:**
A continuación se presentan los detalles de las farmacias encontradas en la comuna de interés:

{farmacias_encontradas}

**Instrucciones para Responder:**
- Proporciona una respuesta clara y concisa.
- Asegúrate de mencionar la comuna y resaltar las farmacias que están de turno.
- Incluye la dirección, el teléfono y el horario de funcionamiento de cada farmacia.
- Si hay varias farmacias, organiza la información de manera que sea fácil de entender para el usuario.
- Si alguna farmacia no está de turno, inclúyela en la lista pero menciona que no está de turno.

**Formato de Respuesta:**
Proporciona la respuesta en un formato amigable para el usuario, por ejemplo:

1. **Farmacia:** CRUZ VERDE
   - **Dirección:** DIRECCIÓN 1
   - **Teléfono:** +562414551
   - **Horario:** 08:00 a 20:00
   - **En turno:** Sí

2. **Farmacia:** BOTIQUÍN CENTRO MEDICO LIMACHE
   - **Dirección:** DIRECCIÓN 5
   - **Teléfono:** +5633413336
   - **Horario:** 09:00 a 21:00
   - **En turno:** No

**Ejemplos:**

**Ejemplo 1:**
**Pregunta del Usuario:** "¿Cuáles son las farmacias en LIMACHE?"
**Respuesta esperada:**
"En LIMACHE, he encontrado las siguientes farmacias:

1. **Farmacia:** CRUZ VERDE
   - **Dirección:** DIRECCIÓN 1
   - **Teléfono:** +562414551
   - **Horario:** 08:00 a 20:00
   - **En turno:** Sí

2. **Farmacia:** BOTIQUÍN CENTRO MEDICO LIMACHE
   - **Dirección:** DIRECCIÓN 5
   - **Teléfono:** +5633413336
   - **Horario:** 09:00 a 21:00
   - **En turno:** No


**Ejemplo 2:**
**Pregunta del Usuario:** "¿Cuáles son las farmacias en Providencia que están de turno?"
**Respuesta esperada:**
"En Providencia, he encontrado las siguientes farmacias que están de turno:

1. **Farmacia:** SALCOBRAND
   - **Dirección:** DIRECCIÓN 2
   - **Teléfono:** +562414552
   - **Horario:** 08:30 a 22:00
   - **En turno:** Sí


Proporciona la respuesta siguiendo estas directrices.
""")
    return response_prompt_template        



def get_respuesta_final():
    pass

