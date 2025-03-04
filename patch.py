#!/usr/bin/env python3
"""
Script to fix issues in the Especialidades app.
This script adds missing functions and fixes database connection handling.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def apply_helper_functions_patch():
    """Fix helper_functions.py to handle both connection types."""
    logger.info("Fixing helper_functions.py")
    helper_functions_path = "helper_functions.py"
    
    with open(helper_functions_path, "w") as f:
        f.write('''"""
Helper functions to fix missing functions in the main helper.py file.
This is a temporary fix to ensure the application can run without issues.
"""

import streamlit as st
import time
import logging
from sqlalchemy import text

# Configure logging
logger = logging.getLogger(__name__)

def recharge_user_list(conn, es_sql=False):
    """
    Get the list of users from the database.
    
    Args:
        conn: Database connection
        es_sql (bool): Whether this is for SQL specialization
        
    Returns:
        List[str]: List of usernames
    """
    try:
        if hasattr(conn, 'connect'):  # SQLAlchemy Engine
            with conn.connect() as connection:
                if es_sql:
                    query = "SELECT username FROM [dbo].Dim_Users ORDER BY username"
                else:
                    query = "SELECT name FROM [esnowflake].[dbo].Dim_Users ORDER BY name"
                result = connection.execute(text(query))
                return [row[0] for row in result.fetchall()]
        else:  # pyodbc connection
            cursor = conn.cursor()
            if es_sql:
                query = "SELECT username FROM [dbo].Dim_Users ORDER BY username"
            else:
                query = "SELECT name FROM [esnowflake].[dbo].Dim_Users ORDER BY name"
            cursor.execute(query)
            user_list_v = cursor.fetchall()
            return [item[0] for item in user_list_v]
    except Exception as e:
        logger.error(f"Error recharging user list: {str(e)}", exc_info=True)
        return []

def new_user(conn, new_user, message=None, es_sql=False):
    """
    Add a new user to the database.
    
    Args:
        conn: Database connection
        new_user (str): Username to add
        message (str, optional): Message to display
        es_sql (bool): Whether this is for SQL specialization
    """
    try:
        if hasattr(conn, 'connect'):  # SQLAlchemy Engine
            with conn.connect() as connection:
                with connection.begin():
                    if es_sql:
                        connection.execute(
                            text("INSERT INTO [dbo].Dim_Users (username) VALUES (:username)"),
                            {'username': new_user}
                        )
                    else:
                        connection.execute(
                            text("INSERT INTO [esnowflake].[dbo].Dim_Users (name, rango) VALUES (:name, :rango)"),
                            {'name': new_user, 'rango': 'Iniciado'}
                        )
        else:  # pyodbc connection
            cursor = conn.cursor()
            if es_sql:
                cursor.execute(
                    "INSERT INTO [dbo].Dim_Users (username) VALUES (?)",
                    (new_user,)
                )
            else:
                cursor.execute(
                    "INSERT INTO [esnowflake].[dbo].Dim_Users (name, rango) VALUES (?, ?)",
                    (new_user, 'Iniciado')
                )
            conn.commit()

        if message:
            st.success('New user added successfully!')
        
        if 'user' in st.session_state:
            st.session_state["user"] = new_user
        
        if 'lista_plana' in st.session_state:
            st.session_state["lista_plana"] = recharge_user_list(conn, es_sql)
        
        time.sleep(1)
        st.rerun()
    except Exception as e:
        logger.error(f"Error adding new user: {str(e)}", exc_info=True)
        st.error(f'Error adding new user: {str(e)}')

def reset_delete_user(conn, useri, delete, es_sql=False):
    """
    Reset or delete a user from the database.
    
    Args:
        conn: Database connection
        useri (str): Username to reset or delete
        delete (bool): Whether to delete the user (True) or reset (False)
        es_sql (bool): Whether this is for SQL specialization
    """
    action = 'delete' if delete else 'reset'
    
    try:
        if hasattr(conn, 'connect'):  # SQLAlchemy Engine
            with conn.connect() as connection:
                with connection.begin():
                    if es_sql:
                        connection.execute(
                            text("DELETE FROM [dbo].Fact_Answers WHERE username = :username"),
                            {'username': useri}
                        )
                        if delete:
                            connection.execute(
                                text("DELETE FROM [dbo].Dim_Users WHERE username = :username"),
                                {'username': useri}
                            )
                    else:
                        connection.execute(
                            text("DELETE FROM [esnowflake].[dbo].FACT_ANSWERS WHERE user_nickname = :username"),
                            {'username': useri}
                        )
                        connection.execute(
                            text("DELETE FROM [esnowflake].[dbo].FACT_EXAMS WHERE user_nickname = :username"),
                            {'username': useri}
                        )
                        if delete:
                            connection.execute(
                                text("DELETE FROM [esnowflake].[dbo].Dim_Users WHERE name = :username"),
                                {'username': useri}
                            )
        else:  # pyodbc connection
            cursor = conn.cursor()
            if es_sql:
                cursor.execute(
                    "DELETE FROM [dbo].Fact_Answers WHERE username = ?",
                    (useri,)
                )
                if delete:
                    cursor.execute(
                        "DELETE FROM [dbo].Dim_Users WHERE username = ?",
                        (useri,)
                    )
            else:
                cursor.execute(
                    "DELETE FROM [esnowflake].[dbo].FACT_ANSWERS WHERE user_nickname = ?",
                    (useri,)
                )
                cursor.execute(
                    "DELETE FROM [esnowflake].[dbo].FACT_EXAMS WHERE user_nickname = ?",
                    (useri,)
                )
                if delete:
                    cursor.execute(
                        "DELETE FROM [esnowflake].[dbo].Dim_Users WHERE name = ?",
                        (useri,)
                    )
            conn.commit()
        
        st.success("Action completed!")

        if 'lista_plana' in st.session_state:
            st.session_state["lista_plana"] = recharge_user_list(conn, es_sql)
            
        if delete:
            if 'user' in st.session_state:
                st.session_state["user"] = None
        else:
            new_user(conn, useri, es_sql=es_sql)
        
        if 'count_reset' in st.session_state:
            st.session_state["count_reset"] = 0
            
        if 'count_delete' in st.session_state:
            st.session_state["count_delete"] = 0
            
        time.sleep(1)
        st.rerun()
    except Exception as e:
        logger.error(f"Error {action}ing user: {str(e)}", exc_info=True)
        st.error(f'Error {action}ing user: {str(e)}')''')
    
    return True

def add_missing_functions_to_helper():
    """Add missing functions to helper.py."""
    logger.info("Adding missing functions to helper.py")
    helper_path = "helper.py"
    
    missing_functions = '''
# Missing functions added by the patch script

def comparar_respuestas(user_answer, correct_answer):
    """
    Compare user answer with correct answer.
    
    Args:
        user_answer (str or list): User's selected answer(s)
        correct_answer (str or list): Correct answer(s)
        
    Returns:
        bool: True if answers match, False otherwise
    """
    # Convert to lists if not already
    if not isinstance(user_answer, list):
        user_answer = [user_answer]
    if not isinstance(correct_answer, list):
        correct_answer = [correct_answer]
    
    # Sort for comparison
    user_sorted = sorted(user_answer)
    correct_sorted = sorted(correct_answer)
    
    return user_sorted == correct_sorted

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
        user_answer = st.multiselect("Opciones", answers)
    else:
        st.write("**Selecciona la opción correcta:**")
        user_answer = st.radio("Opciones", answers)
    
    # Navigation buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Anterior" if current_idx > 0 else "Saltar"):
            if current_idx > 0:
                st.session_state["current_question"] -= 1
            else:
                st.session_state["current_question"] += 1
            st.rerun()
    
    with col2:
        button_label = "Siguiente" if mode == "examen" else "Comprobar"
        if st.button(button_label):
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

def filtros(especialidad, datos, conn, user, is_exam=False):
    """
    Filter questions based on user selections.
    
    Args:
        especialidad (str): The specialization type
        datos (list): List of all questions with their data
        conn: Database connection
        user (str): Username
        is_exam (bool): Whether in exam mode
        
    Returns:
        list: Filtered questions
    """
    import streamlit as st
    import constantes as c
    import ast
    from sqlalchemy import text
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Question range slider
    values = st.slider(
        "Seleccione rango de preguntas en el que practicar",
        0,
        len(datos),
        (0, len(datos)),
        step=1,
    )

    # Section selection
    secciones = st.multiselect(
        "¿Qué secciones quieres tocar?",
        getattr(c, f"SECCIONES_{especialidad.upper()}"),
    )

    # Apply range filter
    preguntas_filtradas = [
        item for item in datos if values[0] <= item["question_number"] <= values[1]
    ]
    
    # Apply section filter
    if "Todas" not in secciones and secciones:
        preguntas_filtradas = [
            item
            for item in preguntas_filtradas
            if any(area in secciones for area in item["question_area"])
        ]

    # Process additional filters
    if user:
        try:
            aux_opcion = None
            
            # Execute query based on connection type
            if hasattr(conn, 'connect'):  # SQLAlchemy Engine
                with conn.connect() as connection:
                    result = connection.execute(
                        text("EXEC GetQuestionHistory @user=:user"),
                        {"user": user}
                    )
                    aux_opcion = result.fetchall()
            else:  # pyodbc connection
                cursor = conn.cursor()
                cursor.execute(
                    "EXEC GetQuestionHistory @user=?",
                    (user,)
                )
                aux_opcion = cursor.fetchall()
                
            # Additional filters UI
            option = st.multiselect(
                "Otros filtros",
                ["Todas", "Sin hacer", "Falladas en exámenes", "Falladas en práctica"],
            )
            
            # Process filter options
            no_hechas = []
            opcion_examen_falsas = []
            opcion_practicas_falsas = []

            if aux_opcion and len(aux_opcion) > 0:
                if "Falladas en exámenes" in option and aux_opcion[0][1]:
                    opcion_examen_falsas = list(ast.literal_eval(aux_opcion[0][1]))

                if "Falladas en práctica" in option and aux_opcion[0][2]:
                    opcion_practicas_falsas = list(ast.literal_eval(aux_opcion[0][2]))

                if "Sin hacer" in option:
                    hechas = aux_opcion[0][0]
                    if hechas:
                        hechas_lista = ast.literal_eval(hechas)
                        hechas_int = [int(num) for num in list(hechas_lista)]
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
                if "Todas" not in option and option:
                    preguntas_filtradas = [
                        item
                        for item in preguntas_filtradas
                        if item["question_number"] in opcion_final
                    ]
        except Exception as e:
            logger.error(f"Error applying filters: {str(e)}", exc_info=True)
            st.error(f"Error applying filters: {str(e)}")
    
    return preguntas_filtradas

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
    )
    
    # Exam duration
    exam_duration = st.slider(
        "Exam duration (minutes):",
        10,
        120,
        30,
        step=5,
    )
    
    # Random question selection
    random_selection = st.checkbox("Random question selection", value=True)
    
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

def orden_preguntas(question_set):
    """
    Randomize the order of questions.
    
    Args:
        question_set: List of questions to randomize
    
    Returns:
        List: Randomized questions
    """
    import random
    if not question_set:
        return []
    return random.sample(question_set, len(question_set))
'''
    
    # Read current helper.py content
    try:
        with open(helper_path, "r") as f:
            content = f.read()
        
        # Check if functions are already present
        functions_to_check = ["def setexam(", "def filtros(", "def exam_settings(", 
                             "def aux_exam(", "def comparar_respuestas("]
        
        missing = [f for f in functions_to_check if f not in content]
        
        if missing:
            logger.info(f"Adding missing functions: {', '.join(missing)}")
            with open(helper_path, "a") as f:
                f.write(missing_functions)
        else:
            logger.info("All required functions already present in helper.py")
    except Exception as e:
        logger.error(f"Error adding functions to helper.py: {str(e)}", exc_info=True)
        return False
    
    return True

def fix_dependencies():
    """Fix circular dependencies between modules."""
    logger.info("Fixing circular dependencies")
    
    helper_path = "helper.py"
    
    try:
        with open(helper_path, "r") as f:
            content = f.read()
        
        # Find the import section that might create circular dependencies
        import_section = '''try:
    import helper_functions as hf
    # Use helper_functions implementation if available
    recharge_user_list = hf.recharge_user_list
    new_user = hf.new_user
    reset_delete_user = hf.reset_delete_user
except ImportError:
    # Fallback implementations
'''
        
        # Replace with improved version if found
        if "import helper_functions as hf" in content:
            content = content.replace(
                "except ImportError:",
                "except ImportError:\n    # Already implemented fallbacks in helper.py"
            )
            
            with open(helper_path, "w") as f:
                f.write(content)
    except Exception as e:
        logger.error(f"Error fixing dependencies: {str(e)}", exc_info=True)
        return False
    
    return True

def apply_patch():
    """Apply all patches to fix the application."""
    logger.info("Starting application patch")
    
    # Apply fixes
    if apply_helper_functions_patch():
        logger.info("✅ helper_functions.py patched successfully")
    else:
        logger.error("❌ Failed to patch helper_functions.py")
        return False
    
    if add_missing_functions_to_helper():
        logger.info("✅ Missing functions added to helper.py")
    else:
        logger.error("❌ Failed to add missing functions to helper.py")
        return False
    
    if fix_dependencies():
        logger.info("✅ Fixed circular dependencies")
    else:
        logger.error("❌ Failed to fix circular dependencies")
        return False
    
    logger.info("✅ All patches applied successfully!")
    return True

if __name__ == "__main__":
    # Change to the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    logger.info("Applying fixes to the codebase...")
    if apply_patch():
        logger.info("✅ Fixes applied successfully!")
    else:
        logger.error("❌ Failed to apply fixes")
        sys.exit(1)