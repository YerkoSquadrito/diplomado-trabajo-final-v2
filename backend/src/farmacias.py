import sqlite3
import json
from pathlib import Path
import requests  # Para hacer peticiones HTTP
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")

os.environ["LANGCHAIN_API_KEY"] = langchain_api_key
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "TRABAJO-FARMACIAS"

# URLs de las APIs
URL_FARMACIAS = "https://midas.minsal.cl/farmacia_v2/WS/getLocales.php"
URL_FARMACIAS_TURNO = "https://midas.minsal.cl/farmacia_v2/WS/getLocalesTurnos.php"

def descargar_datos(api_url, archivo_destino):
    """Descarga los datos desde la API y los guarda en un archivo JSON."""
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Lanza una excepción para errores HTTP

        data = response.json()

        # Guardar los datos en un archivo JSON
        with open(archivo_destino, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"Datos descargados y guardados en {archivo_destino}")
    except requests.exceptions.RequestException as e:
        print(f"Error al descargar los datos: {e}")

# Función para crear la base de datos y la tabla única
def crear_base_datos(db_name):
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Eliminar la tabla si ya existe
        cursor.execute('DROP TABLE IF EXISTS farmacias_all')

        # Crear una tabla que soporte todas las columnas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS farmacias_all (
                local_id INTEGER PRIMARY KEY,
                local_nombre TEXT,
                comuna_nombre TEXT,
                localidad_nombre TEXT,
                local_direccion TEXT,
                funcionamiento_hora_apertura TEXT,
                funcionamiento_hora_cierre TEXT,
                local_telefono TEXT,
                local_lat REAL,
                local_lng REAL,
                funcionamiento_dia TEXT,
                fuente TEXT,
                en_turno INTEGER
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error al crear la base de datos: {e}")

def es_float(valor):
    """Verifica si un valor puede convertirse a float y está en un formato correcto."""
    try:
        return isinstance(valor, str) and ',' not in valor and float(valor)
    except ValueError:
        return False

def cargar_datos_json(json_file, db_path, fuente, en_turno):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with open(json_file, 'r') as f:
        data = json.load(f)

    for item in data:
        local_lat = item.get('local_lat', None)
        local_lng = item.get('local_lng', None)

        # Validar latitud y longitud antes de la inserción
        if not es_float(local_lat):
            # print(f"Advertencia: Latitud inválida '{local_lat}' en local_id {item['local_id']}. Estableciendo valor None.")
            local_lat = None
        if not es_float(local_lng):
            # print(f"Advertencia: Longitud inválida '{local_lng}' en local_id {item['local_id']}. Estableciendo valor None.")
            local_lng = None

        cursor.execute('''
            INSERT INTO farmacias_all (
                local_id, local_nombre, comuna_nombre, localidad_nombre, 
                local_direccion, funcionamiento_hora_apertura, 
                funcionamiento_hora_cierre, local_telefono, 
                local_lat, local_lng, funcionamiento_dia, fuente, en_turno
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(local_id) DO UPDATE SET
                local_nombre=excluded.local_nombre,
                comuna_nombre=excluded.comuna_nombre,
                localidad_nombre=excluded.localidad_nombre,
                local_direccion=excluded.local_direccion,
                funcionamiento_hora_apertura=excluded.funcionamiento_hora_apertura,
                funcionamiento_hora_cierre=excluded.funcionamiento_hora_cierre,
                local_telefono=excluded.local_telefono,
                local_lat=excluded.local_lat,
                local_lng=excluded.local_lng,
                funcionamiento_dia=excluded.funcionamiento_dia,
                fuente=excluded.fuente,
                en_turno=excluded.en_turno
        ''', (
            int(item['local_id']),
            item.get('local_nombre', None),
            item.get('comuna_nombre', None),
            item.get('localidad_nombre', None),
            item.get('local_direccion', None),
            item.get('funcionamiento_hora_apertura', None),
            item.get('funcionamiento_hora_cierre', None),
            item.get('local_telefono', None),
            float(local_lat) if local_lat else None,
            float(local_lng) if local_lng else None,
            item.get('funcionamiento_dia', None),
            fuente,
            en_turno
        ))

    conn.commit()
    conn.close()
    print(f"Datos insertados/actualizados desde {fuente} en la tabla `farmacias_all`.")

def obtener_estructura_tabla(db_name, table_name='farmacias_all'):
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        cursor.execute(f"PRAGMA table_info({table_name})")
        columnas = cursor.fetchall()

        conn.close()

        estructura = []
        for columna in columnas:
            nombre_columna = columna[1]
            tipo_columna = columna[2]
            
            # Aquí puedes agregar descripciones adicionales para cada columna.
            descripcion = {
                "local_id": "Identificador único de la farmacia.",
                "local_nombre": "Nombre de la farmacia.",
                "comuna_nombre": "Nombre de la comuna donde se encuentra la farmacia.",
                "localidad_nombre": "Nombre de la localidad donde se encuentra la farmacia.",
                "local_direccion": "Dirección física de la farmacia.",
                "funcionamiento_hora_apertura": "Hora de apertura de la farmacia.",
                "funcionamiento_hora_cierre": "Hora de cierre de la farmacia.",
                "local_telefono": "Número de teléfono de la farmacia.",
                "local_lat": "Latitud geográfica de la farmacia.",
                "local_lng": "Longitud geográfica de la farmacia.",
                "funcionamiento_dia": "Día de la semana en que la farmacia está operativa.",
                "fuente": "Origen de los datos (locales o locales_turno).",
                "en_turno": "Indica si la farmacia está de turno (1 para sí, 0 para no)."
            }.get(nombre_columna, "Sin descripción disponible.")

            estructura.append(f"- `{nombre_columna}` ({tipo_columna}): {descripcion}")

        return "\n".join(estructura)
    except Exception as e:
        print(f"Error al obtener la estructura de la tabla: {e}")
        return ""

def ejecutar_consulta_sql(consulta_sql, db_name):
    """Ejecuta la consulta SQL en la base de datos y retorna los resultados."""
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        print(f"Ejecutando consulta SQL: {consulta_sql}")

        cursor.execute(consulta_sql)
        resultados = cursor.fetchall()

        print(f"Consulta SQL ejecutada con éxito. Resultados obtenidos: {len(resultados)} filas.")
        conn.close()
        return resultados
    except Exception as e:
        print(f"Error al ejecutar la consulta SQL: {e}")
        return []

def obtiene_prompt_sql():
    prompt_template = ChatPromptTemplate.from_template("""
        Eres un asistente SQL inteligente que ayuda a generar consultas seguras para una base de datos de farmacias.

        Solo estás autorizado a generar consultas `SELECT`. Nunca debes generar consultas `UPDATE`, `DELETE`, `INSERT` u otras que modifiquen la base de datos. Si se te pide algo distinto a `SELECT`, debes responder: "La consulta solicitada es ilegal y peligrosa."

        La base de datos tiene una tabla llamada `farmacias_all` con las siguientes columnas:

        {estructura_tabla}

        La columna `en_turno` indica si la farmacia está de turno (`1` para sí, `0` para no). Usa esta columna para filtrar farmacias de turno cuando el usuario pregunte específicamente por farmacias que estén de turno o información de ellas.

        Aquí tienes algunos ejemplos de preguntas de usuarios y las correspondientes consultas SQL que deberías generar:

        Ejemplo 1:
        Usuario: "¿Cuáles son las farmacias en la comuna de QUILLOTA?"
        Respuesta en JSON:  "consulta_sql": "SELECT local_nombre, local_direccion FROM farmacias WHERE comuna_nombre = 'QUILLOTA';" 

        Ejemplo 2:
        Usuario: "Quiero saber el nombre y teléfono de las farmacias que están en Santiago Centro y abren antes de las 9 AM."
        Respuesta en JSON:  "consulta_sql": "SELECT local_nombre, local_telefono FROM farmacias WHERE comuna_nombre = 'Santiago Centro' AND funcionamiento_hora_apertura < '09:00';" 

        Ejemplo 3:
        Usuario: "Muestra todas las farmacias con su nombre y horario de cierre en la comuna de Providencia."
        Respuesta en JSON:  "consulta_sql": "SELECT local_nombre, funcionamiento_hora_cierre FROM farmacias WHERE comuna_nombre = 'Providencia';"

        Ejemplo 4:
        Usuario: "¿Qué farmacias de turno están abiertas ahora en la comuna de Las Condes?"
        Respuesta en JSON:  "consulta_sql": "SELECT local_nombre, funcionamiento_hora_cierre FROM farmacias WHERE comuna_nombre = 'Las Condes' AND en_turno = 1;" 

        Ejemplo 5:
        Usuario: "Elimina todas las farmacias en la comuna de Las Condes."
        Respuesta en JSON:  "consulta_sql": "La consulta solicitada es ilegal y peligrosa." 

        Ejemplo 6:
        Usuario: "Actualiza el teléfono de la farmacia con id 10."
        Respuesta en JSON:  "consulta_sql": "La consulta solicitada es ilegal y peligrosa." 

        ** OUTPUT FORMAT: JSON **
        Ahora, genera la consulta SQL en formato JSON para la siguiente pregunta del usuario:

        Usuario: {user_question}
        Respuesta en JSON: 
        "consulta_sql": "" 
        """)
    return prompt_template

def obtiene_prompt_respuesta():
    response_prompt_template = ChatPromptTemplate.from_template("""
    Eres un asistente de farmacias que ayuda a los usuarios a obtener información sobre farmacias. A continuación, se te proporcionarán los resultados de una consulta SQL que contiene información sobre farmacias. 
    Responde al usuario en un lenguaje natural y claro utilizando la información proporcionada.

    Aquí están los resultados de la consulta:
    {resultados_sql}

    Responde a la pregunta del usuario utilizando esta información:
    """)
    return response_prompt_template

def main():
    db_name = Path('db/proj-farmacia.db')
    json_farmacias = Path('data/locales.json')
    json_farmacias_turno = Path('data/locales_turno.json')

    # Crear la base de datos y la tabla única
    crear_base_datos(db_name)

    # Descargar datos de las APIs y guardarlos en archivos JSON
    descargar_datos(URL_FARMACIAS, json_farmacias)
    descargar_datos(URL_FARMACIAS_TURNO, json_farmacias_turno)

    # Cargar los datos de ambos archivos en la misma tabla
    cargar_datos_json(json_farmacias, db_name, fuente="locales", en_turno=0)
    cargar_datos_json(json_farmacias_turno, db_name, fuente="locales_turno", en_turno=1)



#** LLM ** 
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    llm_resp = ChatOpenAI(model="gpt-4o", temperature=0.7)

    prompt_sql = obtiene_prompt_sql()
    response_prompt_template = obtiene_prompt_respuesta()

    estructura_tbl = obtener_estructura_tabla(db_name)

    # Pregunta del usuario
    user_question = "¿me puedes indicar los datos de las farmacias Salcobrand de ñuñoa que estan de turno?".upper()

    # Construye Chains
    chain_sql = prompt_sql | llm | JsonOutputParser()
    chain_response = response_prompt_template | llm_resp | StrOutputParser()

   

    result = chain_sql.invoke({"user_question":user_question,"estructura_tabla":estructura_tbl})

    # La salida ya estará formateada como una consulta SQL pura
    # sql_query = result.content
    query_llm = result['consulta_sql']
    print(query_llm)  # Esto imprimirá solo la consulta SQL limpia

    #** --------------- **

    # Ejecutar la consulta SQL en la base de datos
    resultados = ejecutar_consulta_sql(query_llm, db_name)

    # Imprimir los resultados
    for resultado in resultados:
        print(resultado)

# ** RSPUESTA LENGUAJE NATURAL-----------------------
    respuesta_usuario = chain_response.invoke({"resultados_sql": resultados})

    print(respuesta_usuario)

if __name__ == '__main__':
    main()