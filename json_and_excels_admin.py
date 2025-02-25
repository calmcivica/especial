import streamlit as st
import pandas as pd
import json
import os
import numpy as np
import subprocess
import random
import logging
from io import BytesIO
import ast
import helper as h
from datetime import datetime
from itertools import islice
import pytz

# Configure logging
logger = logging.getLogger(__name__)

# Admin credentials
USERNAME = st.secrets["admin_user"]
PASSWORD = st.secrets["admin_password"]
RUTA = 'jsons/'

############################################################
##  LOGS
############################################################
def log_action(action, especialidad=None, user=None, numero_aleatorio=None):
    """
    Log an action with timestamp and details.
    
    Args:
        action (str): The action performed
        especialidad (str, optional): The specialization type
        user (str, optional): Username
        numero_aleatorio (str, optional): Random number for Excel downloads
    """
    try:
        # Madrid timezone
        madrid_timezone = pytz.timezone("Europe/Madrid")
        timestamp = datetime.now(madrid_timezone).strftime("%Y-%m-%d %H:%M:%S")
        
        # Log message
        log_message = f"[{timestamp}] Acción: {action}"
        if especialidad:
            log_message += f" | Especialidad: {especialidad}"
        if user:
            log_message += f" | Usuario: {user}"
        if numero_aleatorio:
            log_message += f" | Número: {numero_aleatorio}"
        
        # Read existing logs
        try:
            with open("action_log.txt", "r", encoding="utf-8") as log_file:
                logs = log_file.readlines()
        except FileNotFoundError:
            logs = []
        except UnicodeDecodeError:
            # Fallback to latin-1 encoding if UTF-8 fails
            with open("action_log.txt", "r", encoding="latin-1") as log_file:
                logs = log_file.readlines()
        
        # Insert new message at the beginning
        logs.insert(0, log_message + "\n")
        
        # Save the file with messages in descending order
        with open("action_log.txt", "w", encoding="utf-8") as log_file:
            log_file.writelines(logs)
        
        # Log to console
        logger.info(log_message)
    except Exception as e:
        logger.error(f"Error logging action: {str(e)}", exc_info=True)

def read_action_log():
    """
    Read the action log file.
    
    Returns:
        List[str]: Last 50 log entries
    """
    try:
        # Read only the first 50 lines
        with open("action_log.txt", "r", encoding="utf-8") as log_file:
            logs = list(islice(log_file, 50))
        return logs
    except UnicodeDecodeError:
        # Fallback to latin-1 encoding if UTF-8 fails
        try:
            with open("action_log.txt", "r", encoding="latin-1") as log_file:
                logs = list(islice(log_file, 50))
            return logs
        except Exception as e:
            logger.error(f"Error reading log file: {str(e)}", exc_info=True)
            return ["Error reading log file."]
    except FileNotFoundError:
        return ["No se ha encontrado el archivo de log o está vacío."]
    except Exception as e:
        logger.error(f"Error reading action log: {str(e)}", exc_info=True)
        return ["Error reading log file."]

def fetch_download_records(conn):
    """
    Fetch records of Excel downloads from the database.
    
    Args:
        conn: Database connection
        
    Returns:
        pd.DataFrame: Download records
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 10 name, id_excel, fecha_descarga FROM [esnowflake].[dbo].excel")
        records = cursor.fetchall()
        
        # Format dates
        formatted_records = [
            (name, id_excel, fecha_descarga.strftime("%Y-%m-%d %H:%M:%S.%f") 
             if isinstance(fecha_descarga, datetime) else fecha_descarga)
            for name, id_excel, fecha_descarga in records
        ]
        
        # Create DataFrame
        df = pd.DataFrame(formatted_records, columns=["name", "id_excel", "fecha_descarga"])
        return df
    except Exception as e:
        logger.error(f"Error fetching download records: {str(e)}", exc_info=True)
        return pd.DataFrame(columns=["name", "id_excel", "fecha_descarga"])

############################################################
# Excel and JSON functions
############################################################
def create_excel(especialidad):
    """
    Create an Excel file from JSON data.
    
    Args:
        especialidad (str): The specialization type
        
    Returns:
        pd.DataFrame: The data as a DataFrame
    """
    try:
        # Get JSON file path
        if especialidad == 'snowflake_pro':
            nombre_fichero = os.path.join(RUTA, 'snowflake_pro_examtopics')
        elif especialidad == 'snowflake_arch':
            nombre_fichero = os.path.join(RUTA, 'snowflake_arch_examtopics')
        elif especialidad == 'dbt':
            nombre_fichero = os.path.join(RUTA, 'dbt_examtopics')
        elif especialidad == 'google':
            nombre_fichero = os.path.join(RUTA, 'google_examtopics')
        else:
            raise ValueError(f"Unsupported specialization: {especialidad}")
        
        nombre_completo = nombre_fichero + '.json'
        
        # Read JSON file
        with open(nombre_completo, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Transform data for Excel
        rows = []
        for question in data:
            row = {
                "question_number": question.get("question_number"),
                "question_area": question.get("question_area", []),
                "question": question.get("question"),
                "question_extra_info": question.get("question_extra_info", ""),
                "answers": question.get("answers", []),
                "correct_answer": question.get("correct_answer", []),
                "explanation": question.get("explanation", "").replace("\n", " ").replace("\r", ""),
                "reference": question.get("reference", [])
            }
            rows.append(row)
        
        # Convert to DataFrame
        df = pd.DataFrame(rows)
        return df
    except Exception as e:
        logger.error(f"Error creating Excel: {str(e)}", exc_info=True)
        st.error(f"Error creating Excel: {str(e)}")
        return pd.DataFrame()

def generar_numero_aleatorio():
    """
    Generate a random 10-digit number.
    
    Returns:
        str: 10-digit random number
    """
    return ''.join([str(random.randint(0, 9)) for _ in range(10)])

@st.cache_data
def download_excel(especialidad):
    """
    Prepare an Excel file for download.
    
    Args:
        especialidad (str): The specialization type
        
    Returns:
        Tuple: BytesIO object, filename, and random number
    """
    try:
        df = create_excel(especialidad)
        numero_aleatorio = generar_numero_aleatorio()
        
        # Create Excel file
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=numero_aleatorio, index=False)
        excel_buffer.seek(0)
        
        nombre_fichero = especialidad + '.xlsx'
        return excel_buffer, nombre_fichero, numero_aleatorio
    except Exception as e:
        logger.error(f"Error preparing Excel for download: {str(e)}", exc_info=True)
        st.error(f"Error preparing Excel for download: {str(e)}")
        return BytesIO(), f"{especialidad}.xlsx", generar_numero_aleatorio()

def insert_download_db(username, numero_aleatorio, especialidad):
    """
    Insert a record of Excel download into the database.
    
    Args:
        username (str): Username
        numero_aleatorio (str): Random number for the Excel sheet
        especialidad (str): The specialization type
    """
    try:
        conn = h.init_connection(especialidad)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO [esnowflake].[dbo].excel (name, id_excel, fecha_descarga) VALUES (?, ?, GETDATE())",
            (username, numero_aleatorio)
        )
        conn.commit()
        logger.info(f"Executed insert for Excel download: {username}, {numero_aleatorio}")
        log_action("Creación de Excel para descarga", especialidad, username, numero_aleatorio)
    except Exception as e:
        logger.error(f"Error inserting download record: {str(e)}", exc_info=True)

def save_to_json_append(new_data, especialidad, user=None):
    """
    Append new data to a JSON file.
    
    Args:
        new_data (List[Dict]): New data to append
        especialidad (str): The specialization type
        user (str, optional): Username
    """
    try:
        filename = os.path.join(RUTA, f"{especialidad}_examtopics.json")
        
        # Check if file exists
        if os.path.exists(filename):
            # Read existing JSON
            with open(filename, "r", encoding="utf-8") as json_file:
                try:
                    existing_data = json.load(json_file)
                    if isinstance(existing_data, dict):  # Convert dict to list
                        existing_data = [existing_data]
                except json.JSONDecodeError:
                    existing_data = []
            
            # Append new data
            existing_data.extend(new_data)
            
            # Write updated data
            with open(filename, "w", encoding="utf-8") as json_file:
                json.dump(existing_data, json_file, indent=4, ensure_ascii=False)
                json_file.truncate()  # Truncate if new content is shorter
        else:
            # Create new file
            with open(filename, "w", encoding="utf-8") as json_file:
                json.dump(new_data, json_file, indent=4, ensure_ascii=False)
        
        st.success(f"Datos añadidos exitosamente al archivo {filename}")
        log_action("Datos añadidos a JSON (modo append)", especialidad, user)
    except Exception as e:
        logger.error(f"Error saving to JSON: {str(e)}", exc_info=True)
        st.error(f"Error saving to JSON: {str(e)}")

def delete_question_by_number(especialidad, question_number, user=None):
    """
    Delete a question from a JSON file by question number.
    
    Args:
        especialidad (str): The specialization type
        question_number (int): Question number to delete
        user (str, optional): Username
    """
    try:
        filename = os.path.join(RUTA, f"{especialidad}_examtopics.json")
        
        # Check if file exists
        if not os.path.exists(filename):
            st.error("El archivo JSON no existe.")
            return
        
        # Read current JSON
        with open(filename, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        
        # Filter out the question to delete
        updated_data = [question for question in data if question.get("question_number") != question_number]
        
        # Check if any question was deleted
        if len(data) == len(updated_data):
            st.warning(f"No se encontró ninguna pregunta con question_number {question_number}.")
            return
        
        # Save updated JSON
        with open(filename, "w", encoding="utf-8") as json_file:
            json.dump(updated_data, json_file, indent=4, ensure_ascii=False)
        
        st.success(f"La pregunta con question_number {question_number} ha sido eliminada.")
        log_action(f"Pregunta eliminada (question_number {question_number})", especialidad, user)
    except Exception as e:
        logger.error(f"Error deleting question: {str(e)}", exc_info=True)
        st.error(f"Error deleting question: {str(e)}")

def admin_delete_question():
    """Display the interface to delete a question."""
    try:
        st.subheader("Eliminar pregunta por número")
        
        # Select specialization
        especialidad = st.selectbox(
            "Selecciona la especialidad:", 
            ["snowflake_pro", "snowflake_arch", "dbt", "google"]
        )
        
        # Input question number
        question_number = st.number_input(
            "Ingrese el question_number de la pregunta a eliminar:", 
            min_value=1, 
            step=1
        )
        
        # Delete button
        if st.button("Eliminar pregunta"):
            delete_question_by_number(especialidad, question_number)
    except Exception as e:
        logger.error(f"Error in delete question interface: {str(e)}", exc_info=True)
        st.error(f"Error: {str(e)}")

def restart_docker_container(user=None):
    """
    Restart the Docker container.
    
    Args:
        user (str, optional): Username
    """
    try:
        st.warning("Reiniciando el proyecto en Docker...")
        
        # Command to restart the container
        command = 'sh -c "sleep 1; kill 1"'
        try:
            subprocess.run(command, shell=True, check=True)
            st.success("El proyecto se ha reiniciado exitosamente.")
            log_action("Reinicio del contenedor Docker", None, user)
        except subprocess.CalledProcessError:
            st.error("Error al intentar reiniciar el proyecto.")
    except Exception as e:
        logger.error(f"Error restarting Docker container: {str(e)}", exc_info=True)
        st.error(f"Error: {str(e)}")

def process_excel_file(uploaded_file):
    """
    Process an uploaded Excel file.
    
    Args:
        uploaded_file: The uploaded file
        
    Returns:
        List[Dict]: Processed data
    """
    try:
        df = pd.read_excel(uploaded_file)
        df = df.replace({np.nan: None})
        
        # Convert DataFrame to list of dictionaries
        new_data = []
        for _, row in df.iterrows():
            # Build dictionary row by row
            row_data = {
                "question_number": row["question_number"],
                "question_area": ast.literal_eval(row["question_area"]) if row["question_area"] else [],
                "question": row["question"],
                "answers": ast.literal_eval(row["answers"]) if row["answers"] else [],
                "correct_answer": ast.literal_eval(row["correct_answer"]) if row["correct_answer"] else [],
                "explanation": row["explanation"].replace("\r", "").replace("\n", "\n") if row["explanation"] else "",
                "reference": ast.literal_eval(row["reference"]) if row["reference"] else []
            }
            
            # Add question_extra_info if present
            if "question_extra_info" in df.columns and row["question_extra_info"] is not None:
                row_data["question_extra_info"] = row["question_extra_info"]
            
            new_data.append(row_data)
        
        return new_data
    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}", exc_info=True)
        st.error(f"Error processing Excel file: {str(e)}")
        return []

def process_json_file(uploaded_file):
    """
    Process an uploaded JSON file.
    
    Args:
        uploaded_file: The uploaded file
        
    Returns:
        List[Dict]: Processed data
    """
    try:
        new_data = json.load(uploaded_file)
        if isinstance(new_data, dict):
            new_data = [new_data]
        return new_data
    except Exception as e:
        logger.error(f"Error processing JSON file: {str(e)}", exc_info=True)
        st.error(f"Error processing JSON file: {str(e)}")
        return []

def download_specialty_json(especialidad):
    """
    Prepare a JSON file for download.
    
    Args:
        especialidad (str): The specialization type
        
    Returns:
        Tuple: BytesIO object, filename, and mime type
    """
    try:
        filename = os.path.join(RUTA, f"{especialidad}_examtopics.json")
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as file:
                json_data = file.read()
            return BytesIO(json_data.encode()), f"{especialidad}_examtopics.json", "application/json"
        else:
            st.warning(f"No existe un archivo JSON para la especialidad {especialidad}.")
            return None, None, None
    except Exception as e:
        logger.error(f"Error preparing JSON for download: {str(e)}", exc_info=True)
        st.error(f"Error: {str(e)}")
        return None, None, None

def load_json(especialidad):
    """
    Load a JSON file.
    
    Args:
        especialidad (str): The specialization type
        
    Returns:
        Dict: The loaded JSON data
    """
    try:
        filename = os.path.join(RUTA, f"{especialidad}_examtopics.json")
        
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
            return data
        else:
            st.warning(f"No existe un archivo JSON para la especialidad {especialidad}.")
            return None
    except Exception as e:
        logger.error(f"Error loading JSON: {str(e)}", exc_info=True)
        st.error(f"Error loading JSON: {str(e)}")
        return None

def save_json(data, especialidad):
    """
    Save data to a JSON file.
    
    Args:
        data (Dict): Data to save
        especialidad (str): The specialization type
    """
    try:
        filename = os.path.join(RUTA, f"{especialidad}_examtopics.json")
        
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        
        st.success(f"Pregunta modificada guardada exitosamente en {filename}")
    except Exception as e:
        logger.error(f"Error saving JSON: {str(e)}", exc_info=True)
        st.error(f"Error saving JSON: {str(e)}")

def delete_all_questions(especialidad, user=None):
    """
    Delete all questions for a specialization.
    
    Args:
        especialidad (str): The specialization type
        user (str, optional): Username
    """
    try:
        filename = os.path.join(RUTA, f"{especialidad}_examtopics.json")
        
        # Check if file exists
        if os.path.exists(filename):
            # Empty the JSON file
            with open(filename, "w", encoding="utf-8") as json_file:
                json.dump([], json_file, indent=4, ensure_ascii=False)
            
            st.success(f"Todas las preguntas de la especialidad '{especialidad}' han sido eliminadas.")
            log_action("Todas las preguntas eliminadas", especialidad, user)
        else:
            st.warning(f"No se encontró un archivo JSON para la especialidad '{especialidad}'.")
    except Exception as e:
        logger.error(f"Error deleting all questions: {str(e)}", exc_info=True)
        st.error(f"Error: {str(e)}")

def save_image(uploaded_file, especialidad, user=None):
    """
    Save an uploaded image.
    
    Args:
        uploaded_file: The uploaded image
        especialidad (str): The specialization type
        user (str, optional): Username
    """
    try:
        # Create directory if it doesn't exist
        folder_path = os.path.join("static", especialidad)
        os.makedirs(folder_path, exist_ok=True)
        
        # Save the image
        image_path = os.path.join(folder_path, uploaded_file.name)
        with open(image_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"La imagen '{uploaded_file.name}' ha sido guardada en la carpeta '{especialidad}'.")
        log_action(f"Imagen '{uploaded_file.name}' guardada", especialidad, user)
    except Exception as e:
        logger.error(f"Error saving image: {str(e)}", exc_info=True)
        st.error(f"Error saving image: {str(e)}")

def delete_image(image_name, especialidad, user=None):
    """
    Delete an image.
    
    Args:
        image_name (str): Image filename
        especialidad (str): The specialization type
        user (str, optional): Username
    """
    try:
        # Get folder path
        folder_path = os.path.join("static", especialidad)
        
        # Check if folder exists
        if not os.path.exists(folder_path):
            st.error(f"La carpeta '{especialidad}' no existe.")
            return
        
        # Get image path
        image_path = os.path.join(folder_path, image_name)
        
        # Check if image exists
        if not os.path.isfile(image_path):
            st.error(f"La imagen '{image_name}' no se encuentra en la carpeta '{especialidad}'.")
            return
        
        # Delete the image
        os.remove(image_path)
        st.success(f"La imagen '{image_name}' ha sido eliminada de la carpeta '{especialidad}'.")
        log_action(f"Imagen '{image_name}' eliminada", especialidad, user)
    except Exception as e:
        logger.error(f"Error deleting image: {str(e)}", exc_info=True)
        st.error(f"Error deleting image: {str(e)}")

def show_admin_panel():
    """Display the admin panel."""
    st.header("Panel de Administración")
    
    # Authentication
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
            logger.error(f"Error in admin login: {str(e)}", exc_info=True)
            st.error(f"Error en el login: {str(e)}")
    
    # Admin panel (only shown when authenticated)
    if st.session_state.get("authenticated", False):
        try:
            # Add questions section
            with st.expander("❇️ Añadir preguntas"):
                st.subheader("Subir archivo de preguntas para especialidades")
                
                especialidad = st.selectbox(
                    "Selecciona la especialidad:", 
                    ["snowflake_pro", "snowflake_arch", "dbt", "google"], 
                    key='modificar'
                )
                
                uploaded_file = st.file_uploader(
                    "Sube un archivo Excel/JSON con el formato requerido", 
                    type=["xlsx", "json"]
                )
                
                if uploaded_file is not None:
                    if uploaded_file.name.endswith(".xlsx"):
                        # Process Excel file
                        new_data = process_excel_file(uploaded_file)
                    elif uploaded_file.name.endswith(".json"):
                        # Process JSON file
                        new_data = process_json_file(uploaded_file)
                    
                    st.write("Contenido del archivo subido:")
                    st.write(new_data)
                    
                    if st.button("Guardar en JSON (modo append)"):
                        save_to_json_append(new_data, especialidad)
            
            # Download JSON section
            with st.expander("❇️ Descargar archivos JSON de especialidades"):
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
            
            # Upload images section
            with st.expander("❇️ Añadir imágenes a la especialidad"):
                st.subheader("Subir imágenes para la especialidad seleccionada")
                
                # Select specialization
                especialidad_imagen = st.selectbox(
                    "Selecciona la especialidad para añadir imágenes:", 
                    ["snowflake_pro", "snowflake_arch", "dbt", "google"], 
                    key="add_image"
                )
                
                # Upload image
                uploaded_image = st.file_uploader("Sube una imagen", type=["jpg", "jpeg", "png", "gif"])
                
                # Save image button
                if uploaded_image is not None:
                    if st.button("Guardar imagen"):
                        save_image(uploaded_image, especialidad_imagen)
            
            # View logs section
            with st.expander("📜 Ver log de acciones"):
                st.subheader("Registro de acciones")
                logs = read_action_log()
                
                # Create scrollable container
                with st.container():
                    st.write(
                        "<div style='max-height: 300px; overflow-y: auto;'>"
                        + "".join(f"<p>{log.strip()}</p>" for log in logs)
                        + "</div>",
                        unsafe_allow_html=True,
                    )
            
            # View images section
            with st.expander("📜 Ver imagenes dentro log de acciones"):
                st.subheader("Imagenes guardadas")
                selected_especialidad = st.selectbox(
                    "Selecciona la especialidad para cargar imágenes:",
                    ["snowflake_pro", "snowflake_arch", "dbt", "google"]
                )
                
                # Get logs
                logs = read_action_log()
                
                # Extract image info from logs
                images_info = []
                for log in logs:
                    if "guardada" in log and selected_especialidad in log:
                        try:
                            # Extract image name between single quotes
                            parts = log.split("'")
                            if len(parts) >= 3:
                                image_name = parts[1]
                                images_info.append((image_name, selected_especialidad))
                        except Exception:
                            pass
                
                # Show images
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
            
            # View downloads section
            with st.expander("📊 Ver registros de descargas en la base de datos"):
                st.subheader("Registros de descargas")
                try:
                    conn = h.init_connection("snowflake_pro")  # Use any type
                    if conn:
                        download_records_df = fetch_download_records(conn)
                        st.dataframe(download_records_df)
                    else:
                        st.warning("Conexión a la base de datos no disponible.")
                except Exception as e:
                    logger.error(f"Error fetching download records: {str(e)}", exc_info=True)
                    st.error(f"Error: {str(e)}")
            
            # Delete image section
            with st.expander("⛔Borrar imagen"):
                st.subheader("Eliminar imagen de una pregunta por número")
                st.write("Si es la imagen en la zona de la pregunta, escribe el número de la pregunta.\n Ej: 1.png Si quieres borrar la imagen en la zona de la solución, escribe el número de la pregunta, seguido por '_sol'. Ej: 1_sol.png")
                
                # Select specialization
                especialidad_borrar = st.selectbox(
                    "Selecciona la especialidad para borrar preguntas:", 
                    ["snowflake_pro", "snowflake_arch", "dbt", "google"], 
                    key="delete_image"
                )
                
                # Input question number
                question_number = st.number_input(
                    "Ingrese el question_number de la pregunta a eliminar:", 
                    min_value=1, 
                    step=1, 
                    key="delete_image_number"
                )
                image_name = f"{question_number}.png"
                
                # Button to delete
                if st.button("Eliminar imagen de pregunta"):
                    delete_image(image_name, especialidad_borrar)
            
            # Delete question section
            with st.expander("⛔Borrar preguntas"):
                st.subheader("Eliminar pregunta por número")
                
                # Select specialization
                especialidad_borrar = st.selectbox(
                    "Selecciona la especialidad para borrar preguntas:", 
                    ["snowflake_pro", "snowflake_arch", "dbt", "google"], 
                    key="delete_question"
                )
                
                # Input question number
                question_number = st.number_input(
                    "Ingrese el question_number de la pregunta a eliminar:", 
                    min_value=1, 
                    step=1
                )
                
                # Button to delete
                if st.button("Eliminar pregunta"):
                    delete_question_by_number(especialidad_borrar, question_number)
            
            # Delete all questions section
            with st.expander("⛔Borrar todas las preguntas de una especialidad"):
                st.subheader("Eliminar todas las preguntas")
                
                # Select specialization
                especialidad_borrar_todas = st.selectbox(
                    "Selecciona la especialidad para borrar todas las preguntas:", 
                    ["snowflake_pro", "snowflake_arch", "dbt", "google"], 
                    key="delete_all"
                )
                
                # Button to delete all
                if st.button("Borrar todas las preguntas"):
                    delete_all_questions(especialidad_borrar_todas)
            
            # Restart Docker section
            with st.expander("🔄 - Reiniciar el proyecto en Docker"):
                if st.button("Reiniciar Docker"):
                    restart_docker_container()
        except Exception as e:
            logger.error(f"Error in admin panel: {str(e)}", exc_info=True)
            st.error(f"Error: {str(e)}")