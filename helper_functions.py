"""
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
        conn: Database connection (either pyodbc connection or SQLAlchemy engine)
        es_sql (bool): Whether this is for SQL specialization
        
    Returns:
        List[str]: List of usernames
    """
    try:
        # Check if connection is SQLAlchemy engine
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
        st.error(f'Error {action}ing user: {str(e)}')