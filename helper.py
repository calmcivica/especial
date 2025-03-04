import os



import random



import json



import streamlit as st



import uuid



import time



import threading



import datetime



import pyodbc



import ast



import logging



import constantes as c



from pathlib import Path



from sqlalchemy import create_engine, text



from docx import Document



from typing import List, Dict, Any, Tuple, Optional, Union







# Configure logging





logger = logging.getLogger(__name__)




# Dictionary to cache query results
_query_cache = {}

@st.cache_resource(ttl=7200, show_spinner=False)  # Cache for 2 hours, hide spinner
def init_connection(especialidad):
    """
    Initialize database connection based on the specialization type.
    
    Args:
        especialidad (str): The type of specialization (snowflake_pro, snowflake_arch, dbt, google, sql)
        
    Returns:
        Connection object: Either a pyodbc connection or SQLAlchemy engine
        
    Raises:
        Exception: If there's an error initializing the connection
    """
    try:
        if especialidad in ['snowflake_pro', 'snowflake_arch', 'dbt', 'google']:
            tipo = 'especialidades'
            conn_string = (
                "DRIVER={ODBC Driver 17 for SQL Server};SERVER="
                + st.secrets["server"]
                + ";DATABASE="
                + st.secrets[f"database_{tipo}"]
                + ";UID="
                + st.secrets[f"username_{tipo}"]
                + ";PWD="
                + st.secrets[f"password_{tipo}"]
                + ";Timeout=30;Connection Timeout=30;TrustServerCertificate=yes;"
                + "pooling=yes;Max Pool Size=100;Min Pool Size=10;"
                + "Connection Lifetime=0;Enlist=false;Mars Connection=true"
            )
            # Use SQLAlchemy for all connections with optimized pooling config
            return create_engine(
                f"mssql+pyodbc:///?odbc_connect={conn_string}", 
                pool_pre_ping=True,        # Check connection validity before use
                pool_recycle=3600,         # Recycle connections after 60 minutes
                pool_size=30,              # Increased pool size per Streamlit instance
                max_overflow=40,           # Allow additional connections when pool is full
                pool_timeout=60,           # Wait max 60s for available connection
                pool_use_lifo=True,        # Last in first out reduces overall connections
                echo=False                 # Disable SQL logging for performance
            )
                
        elif especialidad == 'sql':
            tipo = 'sql'
            connection_str = (
                "mssql+pyodbc://"
                + st.secrets[f"username_{tipo}"]
                + ":"
                + st.secrets[f"password_{tipo}"]
                + "@"
                + st.secrets["server"]
                + "/"
                + st.secrets[f"database_{tipo}"]
                + "?driver=ODBC+Driver+17+for+SQL+Server"
                + "&TrustServerCertificate=yes"
                + "&connection_timeout=30"
                + "&connect_timeout=30"
            )
            return create_engine(
                connection_str, 
                pool_pre_ping=True,        # Check connection validity before use
                pool_recycle=3600,         # Recycle connections after 60 minutes
                pool_size=30,              # Increased pool size
                max_overflow=40,           # Allow additional connections when pool is full
                pool_timeout=60,           # Wait max 60s for available connection
                pool_use_lifo=True,        # Last in first out reduces overall connections
                echo=False                 # Disable SQL logging for performance
            )
        else:
            raise Exception(f"Unsupported specialization type: {especialidad}")
            
    except Exception as e:
        logger.error(f"Error initializing connection for {especialidad}: {str(e)}", exc_info=True)
        
        # Try again with a basic connection as fallback
        try:
            logger.info(f"Attempting fallback connection for {especialidad}")
            if especialidad in ['snowflake_pro', 'snowflake_arch', 'dbt', 'google']:
                tipo = 'especialidades'
                return pyodbc.connect(
                    "DRIVER={ODBC Driver 17 for SQL Server};SERVER="
                    + st.secrets["server"]
                    + ";DATABASE="
                    + st.secrets[f"database_{tipo}"]
                    + ";UID="
                    + st.secrets[f"username_{tipo}"]
                    + ";PWD="
                    + st.secrets[f"password_{tipo}"]
                    + ";Connection Timeout=30"
                )
            raise Exception("Fallback connection also failed")
        except Exception as fallback_error:
            logger.error(f"Fallback connection failed: {fallback_error}", exc_info=True)
            raise Exception(f"Error initializing connection: {str(e)}")




def open_file(json_file):
    """
    Open and load a JSON file.
    
    Args:
        json_file (str): Path to the JSON file
        
    Returns:
        dict: The loaded JSON data
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as archivo:
            datos = json.load(archivo)
        return datos
    except Exception as e:
        logger.error(f"Error opening file {json_file}: {str(e)}", exc_info=True)
        st.error(f"Error loading data: {str(e)}")
        return []




def get_session_state(key, default_value=None):
    """
    Get a value from session state, initializing it if it doesn't exist.
    
    Args:
        key (str): The session state key
        default_value: The default value if the key doesn't exist
        
    Returns:
        The value from session state
    """
    if key not in st.session_state:
        st.session_state[key] = default_value
    return st.session_state[key]




def set_session_state(key, value):
    """
    Set a value in session state.
    
    Args:
        key (str): The session state key
        value: The value to set
    """
    st.session_state[key] = value




def get_user_none():
    """Get the current user from session state or None if not set.
    
    Returns:
        str or None: The current user
    """
    return get_session_state('user', None)


try:
    import helper_functions as hf
    # Use helper_functions implementation if available
    recharge_user_list = hf.recharge_user_list
    new_user = hf.new_user
    reset_delete_user = hf.reset_delete_user
except ImportError:
    # Already implemented fallbacks in helper.py
    # Fallback implementations
    def recharge_user_list(conn, es_sql=False):
        """
        Get the list of users from the database.
        
        Args:
            conn: Database connection (SQLAlchemy engine)
            es_sql (bool): Whether this is for SQL specialization
            
        Returns:
            List[str]: List of usernames
        """
        try:
            if es_sql:
                query = "SELECT username FROM [dbo].Dim_Users ORDER BY username"
            else:
                query = "SELECT name FROM [esnowflake].[dbo].Dim_Users ORDER BY name"

            result = execute_query(conn, query, fetch_all=True)
            return [row[0] for row in result] if result else []
        except Exception as e:
            logger.error(f"Error recharging user list: {str(e)}", exc_info=True)
            return []

def orden_preguntas(question_set):
    """
    Randomize the order of questions.
    
    Args:
        question_set: List of questions to randomize
    
    Returns:
        List: Randomized questions
    """
    if not question_set:
        return []
    return random.sample(question_set, len(question_set))

# Cache query results for better performance
def execute_query(conn, query, params=None, fetch_all=True, as_dict=False, use_cache=False, cache_ttl=300):
    """Execute a SQL query consistently handling both pyodbc and SQLAlchemy connections.
    
    Args:
        conn: Database connection (either pyodbc connection or SQLAlchemy engine)
        query (str): SQL query to execute
        params (dict or tuple, optional): Parameters for the query
        fetch_all (bool): Whether to fetch all results (True) or just one (False)
        as_dict (bool): Whether to return results as dictionaries (True) or tuples (False)
        use_cache (bool): Whether to cache read-only query results
        cache_ttl (int): Time-to-live for cached results in seconds (default: 5 minutes)
        
    Returns:
        list: Query results
    """
    global _query_cache
    
    # Generate cache key if caching is enabled
    cache_key = None
    if use_cache and query.strip().upper().startswith('SELECT'):
        # Create a unique key for this query and its parameters
        param_str = str(params) if params else 'no_params'
        cache_key = f"{hash(query)}_{hash(param_str)}_{fetch_all}_{as_dict}"
        
        # Check if we have a valid cached result
        if cache_key in _query_cache:
            cached_time, cached_result = _query_cache[cache_key]
            if time.time() - cached_time < cache_ttl:
                return cached_result
    
    try:
        # Check if connection is SQLAlchemy engine
        if hasattr(conn, 'connect'):
            with conn.connect() as connection:
                if params:
                    result = connection.execute(text(query), params)
                else:
                    result = connection.execute(text(query))
                
                if not result.returns_rows:
                    return []
                
                if as_dict:
                    columns = result.keys()
                    if fetch_all:
                        query_result = [dict(zip(columns, row)) for row in result.fetchall()]
                    else:
                        row = result.fetchone()
                        query_result = dict(zip(columns, row)) if row else None
                else:
                    query_result = result.fetchall() if fetch_all else result.fetchone()
        else:
            # Assume it's a pyodbc connection
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if cursor.description is None:  # No results expected
                conn.commit()
                return []
            
            if as_dict:
                columns = [column[0] for column in cursor.description]
                if fetch_all:
                    query_result = [dict(zip(columns, row)) for row in cursor.fetchall()]
                else:
                    row = cursor.fetchone()
                    query_result = dict(zip(columns, row)) if row else None
            else:
                query_result = cursor.fetchall() if fetch_all else cursor.fetchone()
        
        # Cache the result if caching is enabled
        if cache_key:
            _query_cache[cache_key] = (time.time(), query_result)
            
            # Clean up old cache entries
            current_time = time.time()
            _query_cache = {k: v for k, v in _query_cache.items() 
                          if current_time - v[0] < cache_ttl * 2}
                
        return query_result

    except Exception as e:
        logger.error(f"Error executing query: {str(e)}", exc_info=True)
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise Exception(f"Database query error: {str(e)}")



def execute_non_query(conn, query, params=None):
    """
    Execute a non-query SQL statement (INSERT, UPDATE, DELETE).

    
    Args:
        conn: Database connection (either pyodbc connection or SQLAlchemy engine)
        query (str): SQL statement to execute
        params (dict or tuple, optional): Parameters for the statement

        
    Returns:
        int: Number of affected rows
    """
    try:
        # Check if connection is SQLAlchemy engine
        if hasattr(conn, 'connect'):
            with conn.connect() as connection:
                with connection.begin():  # Start a transaction
                    if params:
                        result = connection.execute(text(query), params)
                    else:
                        result = connection.execute(text(query))
                    return result.rowcount
        else:
            # Assume it's a pyodbc connection
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.rowcount
    except Exception as e:
        logger.error(f"Error executing non-query: {str(e)}", exc_info=True)
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise Exception(f"Database update error: {str(e)}")



# Gamification system

def get_user_experience(conn, user, is_sql=False):
    """
    Get a user's current experience points and level.

    
    Args:
        conn: Database connection
        user (str): Username 
        is_sql (bool): Whether this is for SQL specialization

        
    Returns:
        dict: User's experience data
    """
    try:
        if is_sql:
            query = """
            SELECT username, 
                   COALESCE(xp, 0) as xp, 
                   COALESCE(level, 1) as level, 
                   COALESCE(streak_days, 0) as streak_days
            FROM [dbo].Dim_Users 
            WHERE username = :username
            """
        else:
            query = """
            SELECT name as username, 
                   COALESCE(xp, 0) as xp, 
                   COALESCE(level, 1) as level, 
                   rango, 
                   COALESCE(streak_days, 0) as streak_days
            FROM [esnowflake].[dbo].Dim_Users 
            WHERE name = :username
            """
        
        # Use caching for this read-only query
        result = execute_query(conn, query, {"username": user}, fetch_all=False, as_dict=True, use_cache=True)
        
        if not result:
            return {"username": user, "xp": 0, "level": 1, "streak_days": 0, "rango": "Iniciado"}
            
        return result
    except Exception as e:
        logger.error(f"Error getting user experience: {str(e)}", exc_info=True)
        return {"username": user, "xp": 0, "level": 1, "streak_days": 0, "rango": "Iniciado"}


def add_experience(conn, user, xp_amount, reason, is_sql=False):
    """
    Add experience points to a user and update their level if needed.

    
    Args:
        conn: Database connection
        user (str): Username
        xp_amount (int): Amount of XP to add
        reason (str): Reason for the XP gain
        is_sql (bool): Whether this is for SQL specialization

        
    Returns:
        dict: Updated user experience data with level up information
    """
    try:
        # Get current user data
        user_data = get_user_experience(conn, user, is_sql)
        current_xp = user_data.get("xp", 0)
        current_level = user_data.get("level", 1)
        current_rango = user_data.get("rango", "Iniciado")
        

        # Calculate new XP and level
        new_xp = current_xp + xp_amount
        

        # XP required for each level (increases with level)
        level_xp_requirements = {
            1: 100,   # 100 XP for level 1->2
            2: 200,   # 200 XP for level 2->3
            3: 400,   # 400 XP for level 3->4
            4: 800,   # 800 XP for level 4->5
            5: 1600   # 1600 XP for level 5->6
        }
        

        # Calculate new level
        new_level = current_level
        level_up = False
        

        while new_level < 6 and new_xp >= level_xp_requirements.get(new_level, 3000):
            new_xp -= level_xp_requirements.get(new_level, 3000)
            new_level += 1
            level_up = True
        

        # Determine rango based on level
        new_rango = current_rango
        if new_level >= 5:
            new_rango = "Parra"  # Top rank
        elif new_level >= 3:
            new_rango = "Maestro"
        elif new_level >= 2:
            new_rango = "Padawan"
        else:
            new_rango = "Iniciado"
        

        # Update user data in database
        if is_sql:
            query = """
            UPDATE [dbo].Dim_Users 
            SET xp = :xp, level = :level, last_active = CURRENT_TIMESTAMP
            WHERE username = :username
            """
            execute_non_query(conn, query, {
                "xp": new_xp,
                "level": new_level,
                "username": user
            })
        else:
            query = """
            UPDATE [esnowflake].[dbo].Dim_Users 
            SET xp = :xp, level = :level, rango = :rango, last_active = CURRENT_TIMESTAMP
            WHERE name = :username
            """
            execute_non_query(conn, query, {
                "xp": new_xp,
                "level": new_level,
                "rango": new_rango,
                "username": user
            })
        

        # Record XP gain in history
        if is_sql:
            query = """
            INSERT INTO [dbo].Fact_XP_History (username, xp_amount, reason, timestamp)
            VALUES (:username, :xp_amount, :reason, CURRENT_TIMESTAMP)
            """
        else:
            query = """
            INSERT INTO [esnowflake].[dbo].Fact_XP_History (user_nickname, xp_amount, reason, timestamp)
            VALUES (:username, :xp_amount, :reason, CURRENT_TIMESTAMP)
            """
            
        execute_non_query(conn, query, {
            "username": user,
            "xp_amount": xp_amount,
            "reason": reason
        })
        

        # Return updated user data
        return {
            "username": user,
            "xp": new_xp,
            "level": new_level,
            "rango": new_rango,
            "level_up": level_up,
            "xp_gained": xp_amount,
            "reason": reason
        }
    except Exception as e:
        logger.error(f"Error adding user experience: {str(e)}", exc_info=True)
        return None


def update_streak(conn, user, is_sql=False):
    """
    Update a user's streak days if they're active today.

    
    Args:
        conn: Database connection
        user (str): Username
        is_sql (bool): Whether this is for SQL specialization

        
    Returns:
        tuple: (streak_days, is_new_streak_day)
    """
    try:
        # Get user's last active date
        if is_sql:
            query = """
            SELECT username, streak_days, CONVERT(DATE, last_active) as last_date
            FROM [dbo].Dim_Users
            WHERE username = :username
            """
        else:
            query = """
            SELECT name as username, streak_days, CONVERT(DATE, last_active) as last_date
            FROM [esnowflake].[dbo].Dim_Users
            WHERE name = :username
            """
        
        result = execute_query(conn, query, {"username": user}, fetch_all=False, as_dict=True)
        
        if not result:
            return 0, False
            
        # Get streak days and last active date
        streak_days = result.get('streak_days', 0) or 0
        last_date = result.get('last_date')
        

        # Get today's date
        today = datetime.datetime.now().date()
        

        # Check if user was active yesterday
        yesterday = today - datetime.timedelta(days=1)
        

        new_streak_day = False
        

        # If last active date is yesterday, increment streak
        if last_date and (last_date == yesterday or last_date == today):
            if last_date != today:
                streak_days += 1
                new_streak_day = True
                
                # Update streak days in database
                if is_sql:
                    query = """
                    UPDATE [dbo].Dim_Users
                    SET streak_days = :streak_days, last_active = CURRENT_TIMESTAMP
                    WHERE username = :username
                    """
                else:
                    query = """
                    UPDATE [esnowflake].[dbo].Dim_Users
                    SET streak_days = :streak_days, last_active = CURRENT_TIMESTAMP
                    WHERE name = :username
                    """
                
                execute_non_query(conn, query, {
                    "streak_days": streak_days,
                    "username": user
                })
        # If last active date is not yesterday or today, reset streak
        elif last_date != today:
            streak_days = 1
            new_streak_day = True
            

            # Reset streak days in database
            if is_sql:
                query = """
                UPDATE [dbo].Dim_Users
                SET streak_days = 1, last_active = CURRENT_TIMESTAMP
                WHERE username = :username
                """
            else:
                query = """
                UPDATE [esnowflake].[dbo].Dim_Users
                SET streak_days = 1, last_active = CURRENT_TIMESTAMP
                WHERE name = :username
                """
            
            execute_non_query(conn, query, {
                "username": user
            })
        
        return streak_days, new_streak_day
    except Exception as e:
        logger.error(f"Error updating streak: {str(e)}", exc_info=True)
        return 0, False

def setexam(question_set, datos, mode, conn, user, especialidad, exam_time=None):
    """
    Display and handle exam/practice questions.
    
    Args:
        question_set (list): List of question numbers to display
        datos (list): List of all questions with their data
        mode (str): "examen" or "practicar"
        conn: Database connection
        user (str): Username
        especialidad (str): Specialization type
        exam_time (int, optional): Exam duration in minutes
    """
    import streamlit as st
    import time
    import os
    
    # Initialize session state for answers
    if "exam_answers" not in st.session_state:
        st.session_state["exam_answers"] = []
    
    # Handle exam timer
    if mode == "examen":
        if "exam_start_time" not in st.session_state:
            st.session_state["exam_start_time"] = time.time()
        
        elapsed_time = int(time.time() - st.session_state["exam_start_time"])
        remaining_time = exam_time * 60 - elapsed_time if exam_time else 0
        
        if remaining_time <= 0 and exam_time:
            st.error("¡Tiempo agotado!")
            st.session_state["exam_mode"] = 2
            st.rerun()
        
        if exam_time:
            mins, secs = divmod(remaining_time, 60)
            st.write(f"Tiempo restante: {mins:02d}:{secs:02d}")
    
    # Check for empty question set
    if not question_set:
        st.warning("No hay preguntas disponibles")
        return
    
    # Initialize current question index
    if "current_question" not in st.session_state:
        st.session_state["current_question"] = 0
    
    current_idx = st.session_state["current_question"]
    
    # Check if we've completed all questions
    if current_idx >= len(question_set):
        if mode == "examen":
            st.session_state["exam_mode"] = 2
            st.session_state["aux_exam_insert"] = 1
            st.rerun()
        else:
            st.success("¡Has completado todas las preguntas!")
            st.session_state["current_question"] = 0
            st.rerun()
        return
    
    # Get question data
    question_number = question_set[current_idx]
    question_data = next((q for q in datos if q["question_number"] == question_number), None)
    
    if not question_data:
        st.error(f"No se encontró la pregunta {question_number}")
        st.session_state["current_question"] += 1
        st.rerun()
        return
    
    # Display question
    st.subheader(f"Pregunta {current_idx + 1} de {len(question_set)}")
    st.write(f"**Área:** {', '.join(question_data['question_area'])}")
    st.markdown(f"**{question_data['question']}**")
    
    # Display question image if exists
    try:
        image_path = f"static/{especialidad}/{question_number}.png"
        if os.path.exists(image_path):
            st.image(image_path)
    except Exception as e:
        st.error(f"Error displaying image: {str(e)}")
    
    # Display answer options
    answers = question_data.get("answers", [])
    correct_answer = question_data.get("correct_answer", [])
    is_multiple = isinstance(correct_answer, list) and len(correct_answer) > 1
    
    if is_multiple:
        st.write("**Selecciona todas las opciones correctas:**")
        user_answer = st.multiselect("Opciones", answers, key=f"multiselect_{current_idx}")
    else:
        st.write("**Selecciona la opción correcta:**")
        user_answer = st.radio("Opciones", answers, key=f"radio_{current_idx}")
    
    # Navigation buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Anterior" if current_idx > 0 else "Saltar", key=f"prev_btn_{current_idx}"):
            if current_idx > 0:
                st.session_state["current_question"] -= 1
            else:
                st.session_state["current_question"] += 1
            st.rerun()
    
    with col2:
        button_label = "Siguiente" if mode == "examen" else "Comprobar"
        if st.button(button_label, key=f"next_btn_{current_idx}"):
            # Record answer
            if user_answer:
                timestamp = time.time()
                st.session_state["exam_answers"].append({
                    "question_number": question_number,
                    "user_answer": user_answer,
                    "timestamp": timestamp
                })
                
                # Check answer for practice mode
                if mode == "practicar" and user:
                    is_correct = comparar_respuestas(user_answer, correct_answer)
                    pregunta(question_number, user, mode, is_correct, True, conn)
                    
                    if is_correct:
                        st.success("¡Correcto!")
                    else:
                        st.error("Incorrecto")
                        st.write("Respuesta(s) correcta(s):")
                        st.write(correct_answer)
                    
                    if "explanation" in question_data:
                        st.write("Explicación:")
                        st.markdown(question_data["explanation"])
            
            # Move to next question
            st.session_state["current_question"] += 1
            st.rerun()

def comparar_respuestas(user_answer, correct_answer):
    """
    Compare user answers with correct answers.
    
    Args:
        user_answer (List[str]): User's selected answers
        correct_answer (List[str]): Correct answers
        
    Returns:
        int: 1 if correct, 0 if incorrect
    """
    try:
        # Convert single answers to lists
        if isinstance(user_answer, str):
            user_answer = [user_answer]
        if isinstance(correct_answer, str):
            correct_answer = [correct_answer]
            
        # Sort and compare
        user_set = set(str(ans).strip().lower() for ans in user_answer)
        correct_set = set(str(ans).strip().lower() for ans in correct_answer)
        
        return 1 if user_set == correct_set else 0
    except Exception as e:
        logger.error(f"Error comparing answers: {str(e)}", exc_info=True)
        return 0

def filtros(especialidad, datos, conn, user, es_examen=False):
    """
    Apply filters to questions.
    
    Args:
        especialidad (str): The specialization type
        datos (List[Dict]): The questions data
        conn: Database connection
        user (str): Username
        es_examen (bool): Whether this is for exam mode
        
    Returns:
        List[Dict]: Filtered questions
    """
    try:
        # Get question numbers
        question_numbers = [q["question_number"] for q in datos]
        min_q = min(question_numbers) if question_numbers else 0
        max_q = max(question_numbers) if question_numbers else 100
        
        # Question range slider
        values = st.slider(
            "Seleccione rango de preguntas",
            min_value=min_q,
            max_value=max_q,
            value=(min_q, max_q),
            step=1,
            key=f"range_slider_{especialidad}"
        )
        
        # Apply range filter
        preguntas_filtradas = [
            item for item in datos 
            if values[0] <= item["question_number"] <= values[1]
        ]
        
        if not es_examen:
            # Section selection
            secciones = st.multiselect(
                "¿Qué secciones quieres tocar?",
                getattr(c, f"SECCIONES_{especialidad.upper()}"),
                key=f"sections_{especialidad}"
            )
            
            # Apply section filter
            if secciones and "Todas" not in secciones:
                preguntas_filtradas = [
                    item for item in preguntas_filtradas
                    if any(area in secciones for area in item["question_area"])
                ]
                
            # Other filters
            option = st.multiselect(
                "Otros filtros",
                ["Todas", "Sin hacer", "Falladas en exámenes", "Falladas en práctica"],
                key=f"other_filters_{especialidad}"
            )
            
            if user and option:
                # Get question history - use cached query
                result = execute_query(
                    conn,
                    "EXEC GetQuestionHistory @user=:user",
                    {"user": user},
                    fetch_all=False,
                    as_dict=True,
                    use_cache=True
                )
                
                if result:
                    no_hechas = []
                    opcion_examen_falsas = []
                    opcion_practicas_falsas = []
                    
                    # Process filter options
                    if "Falladas en exámenes" in option and result.get("exam_failed"):
                        opcion_examen_falsas = ast.literal_eval(result["exam_failed"])
                        
                    if "Falladas en práctica" in option and result.get("practice_failed"):
                        opcion_practicas_falsas = ast.literal_eval(result["practice_failed"])
                        
                    if "Sin hacer" in option and result.get("done"):
                        hechas = ast.literal_eval(result["done"])
                        hechas_int = [int(num) for num in hechas]
                        no_hechas = [
                            item["question_number"]
                            for item in preguntas_filtradas
                            if item["question_number"] not in hechas_int
                        ]
                        
                    # Combine filter options
                    opcion_final = list(
                        set(no_hechas + opcion_examen_falsas + opcion_practicas_falsas)
                    )
                    
                    # Apply combined filter if not "All"
                    if "Todas" not in option:
                        preguntas_filtradas = [
                            item for item in preguntas_filtradas
                            if item["question_number"] in opcion_final
                        ]
        
        return preguntas_filtradas
    except Exception as e:
        logger.error(f"Error applying filters: {str(e)}", exc_info=True)
        return []

def pregunta(id_pregunta, user, tipo, is_correct, is_answered, conn):
    """
    Record question answer in the database.
    
    Args:
        id_pregunta (int): Question ID
        user (str): Username
        tipo (str): Question type (exam or practice)
        is_correct (bool): Whether the answer was correct
        is_answered (bool): Whether the question was answered
        conn: Database connection
        
    Returns:
        bool: Success status
    """
    try:
        # Insert answer into database
        query = """
        INSERT INTO [esnowflake].[dbo].Fact_Answers 
        (question_id, user_nickname, type, is_correct, is_answered, answer_timestamp)
        VALUES (:id_pregunta, :user, :tipo, :is_correct, :is_answered, CURRENT_TIMESTAMP)
        """
        
        params = {
            "id_pregunta": id_pregunta,
            "user": user,
            "tipo": tipo,
            "is_correct": 1 if is_correct else 0,
            "is_answered": 1 if is_answered else 0
        }
        
        execute_non_query(conn, query, params)
        
        # Award experience for correct answers if in practice mode
        if tipo == "practicar" and is_correct:
            add_experience(conn, user, 5, f"Correct answer to question {id_pregunta}")
            
        return True
    except Exception as e:
        logger.error(f"Error recording question answer: {str(e)}", exc_info=True)
        return False

def exam_settings(preguntas_filtradas):
    """
    Handle exam settings UI.
    
    Args:
        preguntas_filtradas (list): Filtered list of questions
        
    Returns:
        tuple: (num_questions, exam_duration)
    """
    import streamlit as st
    import random
    
    # Number of questions
    total_questions = len(preguntas_filtradas)
    num_questions = st.slider(
        "Number of questions:",
        0,
        total_questions,
        min(total_questions, 10),
        step=1,
        key="exam_questions_count"
    )
    
    # Exam duration
    exam_duration = st.slider(
        "Exam duration (minutes):",
        10,
        120,
        30,
        step=5,
        key="exam_duration"
    )
    
    # Random question selection
    random_selection = st.checkbox("Random question selection", value=True, key="random_selection")
    
    # Store in session state
    st.session_state["random_selection"] = random_selection
    
    # Select questions
    if random_selection and num_questions > 0:
        question_numbers = [q["question_number"] for q in preguntas_filtradas]
        
        if num_questions <= len(question_numbers):
            selected_questions = random.sample(question_numbers, num_questions)
        else:
            selected_questions = question_numbers
    else:
        selected_questions = [q["question_number"] for q in preguntas_filtradas[:num_questions]]
    
    # Store in session state
    st.session_state["question_set"] = selected_questions
    
    return num_questions, exam_duration

def aux_exam(action, exam_duration=None, review_set=None):
    """
    Handle exam actions and state transitions.
    
    Args:
        action (str): The action to take ("empezar", "Inicio", "review")
        exam_duration (int, optional): Exam duration in minutes
        review_set (list, optional): Set of questions to review
    """
    import streamlit as st
    
    if action == "empezar":
        st.session_state["exam_mode"] = 1
        st.session_state["exam_duration"] = exam_duration
        st.session_state["exam_answers"] = []
        st.session_state["current_question"] = 0
        st.session_state["exam_start_time"] = None  # Will be set in setexam
    elif action == "Inicio":
        st.session_state["exam_mode"] = 0
        st.session_state["exam_answers"] = []
        st.session_state["current_question"] = 0
    elif action == "review":
        st.session_state["exam_mode"] = 3
        st.session_state["review_set"] = review_set