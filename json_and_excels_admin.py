import streamlit as st
import pandas as pd
import json
import os
import numpy as np
import subprocess
import random
from io import BytesIO
import ast
import helper as h
from datetime import datetime
from itertools import islice

# Credenciales de acceso
USERNAME = st.secrets["admin_user"]
PASSWORD = st.secrets["admin_password"]
RUTA = 'jsons/'

from datetime import datetime
import pytz

############################################################
##  LOGS
############################################################
# Función para registrar acciones
def log_action(action, especialidad=None, user=None, numero_aleatorio=None):
    # Zona horaria de Madrid
    madrid_timezone = pytz.timezone("Europe/Madrid")
    timestamp = datetime.now(madrid_timezone).strftime("%Y-%m-%d %H:%M:%S")
    
    # Mensaje de log
    log_message = f"[{timestamp}] Acción: {action}"
    if especialidad:
        log_message += f" | Especialidad: {especialidad}"
    if user:
        log_message += f" | Usuario: {user}"
    if numero_aleatorio:
        log_message += f" | Número: {numero_aleatorio}"
    
    # Leer mensajes existentes, agregar nuevo y ordenar
    try:
        with open("action_log.txt", "r") as log_file:
            logs = log_file.readlines()
    except FileNotFoundError:
        logs = []

    # Insertar el mensaje al principio
    logs.insert(0, log_message + "\n")
    
    # Guardar el archivo con los mensajes en orden descendente
    with open("action_log.txt", "w") as log_file:
        log_file.writelines(logs)
    
    # Imprimir en la consola para depuración
    print(log_message)

# Función para leer el archivo de log y mostrarlo
def read_action_log():
    try:
        # Leer solo las primeras 50 líneas del archivo de log
        with open("action_log.txt", "r") as log_file:
            logs = list(islice(log_file, 50))
        return logs
        
    except UnicodeDecodeError:
        # Fallback to latin-1 encoding if UTF-8 fails
        with open("action_log.txt", "r", encoding="latin-1") as log_file:
            logs = list(islice(log_file, 50))    
    return logs if logs else ["No se ha encontrado el archivo de log o está vacío."]
    
# Función para realizar un SELECT en la tabla de SQL Server
def fetch_download_records(conn):
    query = "SELECT TOP 10 * FROM [esnowflake].[dbo].excel"
    cursor = conn.cursor()
    cursor.execute(query)
    records = cursor.fetchall()
    columns = ["name", "id_excel", "fecha_descarga"]
    formatted_records = [
        (name, id_excel, fecha_descarga.strftime("%Y-%m-%d %H:%M:%S.%f") if isinstance(fecha_descarga, datetime) else fecha_descarga)
        for name, id_excel, fecha_descarga in records
    ]
    
    # Create DataFrame with the formatted records
    df = pd.DataFrame(formatted_records, columns=columns)

    return df

############################################################

# Función para crear el CSV
def create_excel(especialidad):
    if especialidad == 'snowflake_pro':
        nombre_fichero = os.path.join(RUTA,'snowflake_pro_examtopics')
    elif especialidad == 'snowflake_arch':
        nombre_fichero = os.path.join(RUTA,'snowflake_arch_examtopics')
    elif especialidad == 'dbt':
        nombre_fichero = os.path.join(RUTA,'dbt_examtopics')
    elif especialidad == 'google':
        nombre_fichero = os.path.join(RUTA,'google_examtopics')
    
    nombre_completo = nombre_fichero + '.json'

    # Leer el archivo JSON
    with open(nombre_completo, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Crear una lista para almacenar los datos transformados
    rows = []

    # Procesar cada pregunta en el archivo JSON
    for question in data:
        # Crear un diccionario para almacenar los datos de cada fila
        row = {
            "question_number": question.get("question_number"),
            "question_area": (question.get("question_area", [])),  # Usamos "; " para separar valores en vez de coma
            "question": question.get("question"),
            "question_extra_info": question.get("question_extra_info", ""),  # Campo opcional
            "answers": (question.get("answers", [])),  # Unimos las respuestas con saltos de línea
            "correct_answer": (question.get("correct_answer", [])),  # Unimos las respuestas correctas con saltos de línea
            "explanation": question.get("explanation").replace("\n", " ").replace("\r", ""),  # Limpiar saltos de línea innecesarios
            "reference": (question.get("reference", []))  # Usamos "; " para unir las referencias con comas
        }
        # Añadir la fila a la lista de filas
        rows.append(row)

    # Convertir la lista de filas en un DataFrame de pandas
    df = pd.DataFrame(rows)
    return df

def generar_numero_aleatorio():
    '''Función para generar un número aleatorio de 10 dígitos'''
    return ''.join([str(random.randint(0, 9)) for _ in range(10)])

@st.cache_data
def download_excel(especialidad):
    df = create_excel(especialidad)
    numero_aleatorio = generar_numero_aleatorio()

    # Crear un archivo Excel con el nombre de la hoja como el número aleatorio
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=numero_aleatorio, index=False)
    excel_buffer.seek(0)
    
    nombre_fichero = especialidad + '.xlsx'
    return excel_buffer, nombre_fichero, numero_aleatorio

def insert_download_db(username, numero_aleatorio, especialidad):
    # Guardar en la base de datos con la query
    conn = h.init_connection(especialidad)
    query = f"INSERT INTO [esnowflake].[dbo].excel (name, id_excel, fecha_descarga) VALUES ('{username}', '{numero_aleatorio}', GETDATE())"
    conn.cursor().execute(query)
    conn.commit()
    print(f"Ejecutada query: {query}")
    log_action("Creación de Excel para descarga", especialidad, username, numero_aleatorio)

# Función para guardar datos en JSON en modo append, asegurando formato JSON correcto
def save_to_json_append(new_data, especialidad, user=None):
    filename = os.path.join(RUTA, f"{especialidad}_examtopics.json")

    # Verificar si el archivo ya existe
    if os.path.exists(filename):
        # Leer el archivo JSON existente
        with open(filename, "r+", encoding="utf-8") as json_file:
            try:
                # Cargar el JSON existente como una lista
                existing_data = json.load(json_file)
                if isinstance(existing_data, dict):  # Si es un dict, conviértelo a una lista
                    existing_data = [existing_data]
            except json.JSONDecodeError:
                existing_data = []

            # Añadir la nueva data al final de la lista
            existing_data.extend(new_data)

            # Volver al inicio del archivo y sobrescribirlo con el contenido actualizado
            json_file.seek(0)
            json.dump(existing_data, json_file, indent=4, ensure_ascii=False)
            json_file.truncate()  # Truncar el archivo si el nuevo contenido es más corto
    else:
        # Crear un nuevo archivo JSON con los datos nuevos
        with open(filename, "w", encoding="utf-8") as json_file:
            json.dump(new_data, json_file, indent=4, ensure_ascii=False)
    
    st.success(f"Datos añadidos exitosamente al archivo {filename}")
    log_action("Datos añadidos a JSON (modo append)", especialidad, user)

# Función para borrar una pregunta en el archivo JSON por question_number
def delete_question_by_number(especialidad, question_number, user=None):
    filename = os.path.join(RUTA, f"{especialidad}_examtopics.json")
    
    # Verificar si el archivo existe
    if not os.path.exists(filename):
        st.error("El archivo JSON no existe.")
        return

    # Leer el contenido actual del archivo JSON
    with open(filename, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)

    # Filtrar las preguntas para excluir la que tiene el question_number especificado
    updated_data = [question for question in data if question.get("question_number") != question_number]

    # Verificar si alguna pregunta fue eliminada
    if len(data) == len(updated_data):
        st.warning(f"No se encontró ninguna pregunta con question_number {question_number}.")
        return

    # Guardar el archivo JSON actualizado
    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(updated_data, json_file, indent=4, ensure_ascii=False)

    st.success(f"La pregunta con question_number {question_number} ha sido eliminada.")
    log_action(f"Pregunta eliminada (question_number {question_number})", especialidad, user)


# Interfaz en Streamlit para borrar una pregunta
def admin_delete_question():
    st.subheader("Eliminar pregunta por número")
    
    # Seleccionar especialidad
    especialidad = st.selectbox("Selecciona la especialidad:", ["snowflake_pro", "snowflake_arch", "dbt", "google"])

    # Input para el número de la pregunta
    question_number = st.number_input("Ingrese el question_number de la pregunta a eliminar:", min_value=1, step=1)

    # Botón para ejecutar la eliminación
    if st.button("Eliminar pregunta"):
        delete_question_by_number(especialidad, question_number)

def restart_docker_container(user=None):
    st.warning("Reiniciando el proyecto en Docker...")
    # Comando para reiniciar el contenedor Docker actual
    # Usamos 'sh -c "sleep 1; kill 1"' para reiniciar el contenedor Docker actual
    command = 'sh -c "sleep 1; kill 1"'
    try:
        subprocess.run(command, shell=True, check=True)
        st.success("El proyecto se ha reiniciado exitosamente.")
        log_action("Reinicio del contenedor Docker", user)
    except subprocess.CalledProcessError:
        st.error("Error al intentar reiniciar el proyecto.")

def process_excel_file(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df = df.replace({np.nan: None})
    
    # Convertir el DataFrame en una lista de diccionarios
    new_data = []
    for _, row in df.iterrows():
        # Construir el diccionario fila por fila
        row_data = {
            "question_number": row["question_number"],
            "question_area": row["question_area"],
            "question": row["question"],
            "answers": ast.literal_eval(row["answers"]) if row["answers"] else [],
            "correct_answer": ast.literal_eval(row["correct_answer"]) if row["correct_answer"] else [],
            "explanation": row["explanation"].replace("\r", "").replace("\n", "\n"),
            "reference": ast.literal_eval(row["reference"]) if row["reference"] else []
        }

        # Agregar 'question_extra_info' solo si existe en el DataFrame y tiene valor
        if "question_extra_info" in df.columns and row["question_extra_info"] is not None:
            row_data["question_extra_info"] = row["question_extra_info"]
        
        new_data.append(row_data)

    return new_data

# Función para procesar archivo JSON y convertirlo en lista de diccionarios
def process_json_file(uploaded_file):
    new_data = json.load(uploaded_file)
    if isinstance(new_data, dict):
        new_data = [new_data]
    return new_data

# Función para descargar el JSON de la especialidad
def download_specialty_json(especialidad):
    filename = os.path.join(RUTA, f"{especialidad}_examtopics.json")
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            json_data = file.read()
        return BytesIO(json_data.encode()), f"{especialidad}_examtopics.json", "application/json"
    else:
        st.warning(f"No existe un archivo JSON para la especialidad {especialidad}.")
        return None, None, None


# Función para cargar el archivo JSON de una especialidad
def load_json(especialidad):
    filename = os.path.join(RUTA, f"{especialidad}_examtopics.json")

    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    else:
        st.warning(f"No existe un archivo JSON para la especialidad {especialidad}.")
        return None

# Función para guardar el archivo JSON de una especialidad
def save_json(data, especialidad):
    filename = os.path.join(RUTA, f"{especialidad}_examtopics.json")

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    st.success(f"Pregunta modificada guardada exitosamente en {filename}")
    print(data)

def delete_all_questions(especialidad, user=None):
    """Elimina todas las preguntas del archivo JSON de la especialidad seleccionada."""
    filename = os.path.join(RUTA, f"{especialidad}_examtopics.json")
    
    # Verificar si el archivo existe
    if os.path.exists(filename):
        # Vaciar el archivo JSON
        with open(filename, "w", encoding="utf-8") as json_file:
            json.dump([], json_file, indent=4, ensure_ascii=False)
        st.success(f"Todas las preguntas de la especialidad '{especialidad}' han sido eliminadas.")
        log_action("Todas las preguntas eliminadas", especialidad, user)

    else:
        st.warning(f"No se encontró un archivo JSON para la especialidad '{especialidad}'.")

def save_image(uploaded_file, especialidad, user=None):
    # Crear la ruta de la carpeta de la especialidad en la carpeta 'static'
    folder_path = os.path.join("static", especialidad)
    
    # Verificar si la carpeta existe; si no, crearla
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # Guardar la imagen en la carpeta correspondiente
    image_path = os.path.join(folder_path, uploaded_file.name)
    with open(image_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success(f"La imagen '{uploaded_file.name}' ha sido guardada en la carpeta '{especialidad}'.")
    log_action(f"Imagen '{uploaded_file.name}' guardada", especialidad, user)

def delete_image(image_name, especialidad, user=None):
    # Crear la ruta de la carpeta de la especialidad en la carpeta 'static'
    folder_path = os.path.join("static", especialidad)

    # Verificar si la carpeta de la especialidad existe
    if not os.path.exists(folder_path):
        st.error(f"La carpeta '{especialidad}' no existe.")
        return

    # Crear la ruta completa de la imagen
    image_path = os.path.join(folder_path, image_name)

    # Verificar si la imagen existe
    if not os.path.isfile(image_path):
        st.error(f"La imagen '{image_name}' no se encuentra en la carpeta '{especialidad}'.")
        return

    # Borrar la imagen
    try:
        os.remove(image_path)
        st.success(f"La imagen '{image_name}' ha sido eliminada de la carpeta '{especialidad}'.")
        log_action(f"Imagen '{image_name}' eliminada", especialidad, user)
    except Exception as e:
        st.error(f"Error al eliminar la imagen '{image_name}': {e}")


def show_admin_panel():
    st.header("Panel de Administración")

    # Verificar si el usuario ya está autenticado
    if not st.session_state.get("authenticated", False):
        try:
            with st.form("login_form"):
                st.write("Ingrese sus credenciales para acceder al panel de administración.")
                username = st.text_input("Usuario")
                password = st.text_input("Contraseña", type="password")
                login_button = st.form_submit_button("Iniciar Sesión")

                if login_button:
                    if username == USERNAME and password == PASSWORD:
                        st.session_state["authenticated"] = True
                        st.success("Autenticación exitosa.")
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos.")
        except Exception as e:
            st.write(f"Hay un error en el login: {e}")

    if st.session_state.get("authenticated", False):
        # Desplegable para añadir preguntas
        with st.expander("❇️ Añadir preguntas"):
            try:
                st.subheader("Subir archivo de preguntas para especialidades")

                especialidad = st.selectbox("Selecciona la especialidad:", ["snowflake_pro", "snowflake_arch", "dbt", "google"], key='modificar')
                
                uploaded_file = st.file_uploader("Sube un archivo Excel/JSON con el formato requerido", type=["xlsx", "json"])

                if uploaded_file is not None:
                    if uploaded_file.name.endswith(".xlsx"):
                        # Procesar archivo Excel
                        new_data = process_excel_file(uploaded_file)
                    elif uploaded_file.name.endswith(".json"):
                        # Procesar archivo JSON
                        new_data = process_json_file(uploaded_file)

                    st.write("Contenido del archivo subido:")
                    st.write(new_data)
                    
                    if st.button("Guardar en JSON (modo append)"):
                        save_to_json_append(new_data, especialidad)
            except Exception as e:
                st.write(f"Hay un error en el añadir preguntas: {e}")

        # Desplegable para descargar archivos JSON de cada especialidad
        with st.expander("❇️ Descargar archivos JSON de especialidades"):
            try:
                st.subheader("Descargar JSON por especialidad")
                for esp in ["snowflake_pro", "snowflake_arch", "dbt", "google"]:
                    download_buffer, file_name, mime_type = download_specialty_json(esp)
                    if download_buffer:
                        st.download_button(
                            label=f"Descargar {esp}",
                            data=download_buffer,
                            file_name=file_name,
                            mime=mime_type
                        )
            except Exception as e:
                st.write(f"Hay un error en el descargar archivos JSON: {e}")

        # Desplegable para subir imágenes a la carpeta 'static'
        with st.expander("❇️ Añadir imágenes a la especialidad"):
            try:
                st.subheader("Subir imágenes para la especialidad seleccionada")

                # Seleccionar la especialidad
                especialidad_imagen = st.selectbox("Selecciona la especialidad para añadir imágenes:", ["snowflake_pro", "snowflake_arch", "dbt", "google"], key="add_image")

                # Cargar la imagen
                uploaded_image = st.file_uploader("Sube una imagen", type=["jpg", "jpeg", "png", "gif"])

                # Guardar la imagen al hacer clic en el botón
                if uploaded_image is not None:
                    if st.button("Guardar imagen"):
                        save_image(uploaded_image, especialidad_imagen)
            except Exception as e:
                st.write(f"Hay un error en el añadir imágenes: {e}")

        # Expander para ver el archivo de log de acciones
        with st.expander("📜 Ver log de acciones"):
            try:
                st.subheader("Registro de acciones")
                logs = read_action_log()
                # Crear un contenedor con un tamaño fijo y añadir scroll
                with st.container():
                    st.write(
                        "<div style='max-height: 300px; overflow-y: auto;'>"
                        + "".join(f"<p>{log.strip()}</p>" for log in logs)
                        + "</div>",
                        unsafe_allow_html=True,
                    )
            except Exception as e:
                st.write(f"Hay un error en el ver logs de acciones: {e}")

        # Expander para ver el archivo de log de acciones
        with st.expander("📜 Ver imagenes dentro log de acciones"):
            try:
                st.subheader("Registro de acciones")
                logs = read_action_log()
                selected_especialidad = st.selectbox(
                "Selecciona la especialidad para cargar imágenes:",
                ["snowflake_pro", "snowflake_arch", "dbt", "google"]
            )
                # Extraer imágenes del log
                images_info = [
                    (log.split("'")[1], log.split(":")[-1].strip())  # (nombre_imagen, especialidad)
                    for log in logs if "guardada" in log and selected_especialidad in log
                ]
                st.warning(images_info)

                if images_info:
                    for image_name, especialidad in images_info:
                        folder_path = os.path.join("static", especialidad)
                        image_path = os.path.join(folder_path, image_name)
                        if os.path.isfile(image_path):
                            st.image(image_path, caption=f"{image_name} - {especialidad}", use_column_width=False)
                        else:
                            st.warning(f"No se encontró la imagen '{image_name}' en la carpeta '{especialidad}'.")
                else:
                    st.info(f"No se encontraron imágenes para la especialidad seleccionada: {selected_especialidad}")

            except Exception as e:
                st.write(f"Hay un error en el ver logs de acciones: {e}")


        # Expander para ver los registros en la tabla de SQL Server
        with st.expander("📊 Ver registros de descargas en la base de datos"):
            try:
                st.subheader("Registros de descargas")
                conn = h.init_connection(especialidad)
                if conn:  # Verifica si la conexión es válida
                    download_records_df = fetch_download_records(conn)
                    st.dataframe(download_records_df)
                else:
                    st.warning("Conexión a la base de datos no disponible.")
            except Exception as e:
                st.write(f"Hay un error en el ver los registros en SQL Server: {e}")

        # Desplegable para borrar imagen
        with st.expander("⛔Borrar imagen"):
            try:
                st.subheader("Eliminar imagen de una pregunta por número")
                st.write("Si es la imagen en la zona de la pregunta, escribe el número de la pregunta.\n Ej: 1. Si quieres borrar la imagen en la zona de la solución, escribe el número de la pregunta, seguido por '_sol'. Ej: 1_sol.png")
                # Selección de especialidad
                especialidad_borrar = st.selectbox("Selecciona la especialidad para borrar preguntas:", ["snowflake_pro", "snowflake_arch", "dbt", "google"])

                # Input para el número de la pregunta
                question_number = st.number_input("Ingrese el question_number de la pregunta a eliminar:", min_value=1, step=1)
                question_number = str(question_number) + ".png"
                # Botón para ejecutar la eliminación
                if st.button("Eliminar imagen de pregunta"):
                    delete_image(question_number, especialidad_borrar)
            except Exception as e:
                st.write(f"Hay un error en el borrar preguntas: {e}")                
        # Desplegable para borrar preguntas
        with st.expander("⛔Borrar preguntas"):
            try:
                st.subheader("Eliminar pregunta por número")

                # Selección de especialidad
                especialidad_borrar = st.selectbox("Selecciona la especialidad para borrar preguntas:", ["snowflake_pro", "snowflake_arch", "dbt", "google"])

                # Input para el número de la pregunta
                question_number = st.number_input("Ingrese el question_number de la pregunta a eliminar:", min_value=1, step=1)

                # Botón para ejecutar la eliminación
                if st.button("Eliminar pregunta"):
                    delete_question_by_number(especialidad_borrar, question_number)
            except Exception as e:
                st.write(f"Hay un error en el borrar preguntas: {e}")

        # Desplegable para borrar todas las preguntas de una especialidad
        with st.expander("⛔Borrar todas las preguntas de una especialidad"):
            try:
                st.subheader("Eliminar todas las preguntas")

                # Selección de la especialidad a borrar
                especialidad_borrar_todas = st.selectbox("Selecciona la especialidad para borrar todas las preguntas:", ["snowflake_pro", "snowflake_arch", "dbt", "google"], key="delete_all")

                # Botón para ejecutar la eliminación de todas las preguntas
                if st.button("Borrar todas las preguntas"):
                    delete_all_questions(especialidad_borrar_todas)
            except Exception as e:
                st.write(f"Error al borrar todas las preguntas: {e}")

        # Botón para reiniciar el contenedor Docker
        with st.expander("🔄 - Reiniciar el proyecto en Docker"):
            try:
                if st.button("Reiniciar Docker"):
                    restart_docker_container()
            except Exception as e:
                st.write(f"Error al reiniciar el proyecto en Dockers: {e}")
