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

@st.cache_resource(ttl=3600)  # Cache for 1 hour, then refresh
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
                + "pooling=yes;Max Pool Size=50;Min Pool Size=5"
            )
            # Use SQLAlchemy for all connections to benefit from connection pooling
            return create_engine(f"mssql+pyodbc:///?odbc_connect={conn_string}", 
                                 pool_pre_ping=True,        # Check connection validity before use
                                 pool_recycle=1800,         # Recycle connections after 30 minutes
                                 pool_size=20,              # Pool size per Streamlit instance
                                 max_overflow=30,           # Allow additional connections when pool is full
                                 pool_timeout=30)           # Wait max 30s for available connection
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
            )
            return create_engine(connection_str, 
                                 pool_pre_ping=True,        # Check connection validity before use
                                 pool_recycle=1800,         # Recycle connections after 30 minutes
                                 pool_size=20,              # Pool size per Streamlit instance
                                 max_overflow=30,           # Allow additional connections when pool is full
                                 pool_timeout=30)           # Wait max 30s for available connection
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
        if es_sql:
            query = "SELECT username FROM [dbo].Dim_Users ORDER BY username"
            result = execute_query(conn, query, fetch_all=True, as_dict=False)
            lista_plana = [row[0] for row in result]
        else:
            query = "SELECT name FROM [esnowflake].[dbo].Dim_Users ORDER BY name"
            result = execute_query(conn, query, fetch_all=True, as_dict=False)
            lista_plana = [row[0] for row in result]
        
        return lista_plana
    except Exception as e:
        logger.error(f"Error recharging user list: {str(e)}", exc_info=True)
        return []
    """
    Get the current user from session state or None if not set.
    
    Returns:
        str or None: The current user
    """
    return get_session_state('user', None)
def execute_query(conn, query, params=None, fetch_all=True, as_dict=False):
    """
    Execute a SQL query consistently handling both pyodbc and SQLAlchemy connections.
    
    Args:
        conn: Database connection (either pyodbc connection or SQLAlchemy engine)
        query (str): SQL query to execute
        params (dict or tuple, optional): Parameters for the query
        fetch_all (bool): Whether to fetch all results (True) or just one (False)
        as_dict (bool): Whether to return results as dictionaries (True) or tuples (False)
        
    Returns:
        list: Query results
    """
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
                        return [dict(zip(columns, row)) for row in result.fetchall()]
                    else:
                        row = result.fetchone()
                        return dict(zip(columns, row)) if row else None
                else:
                    return result.fetchall() if fetch_all else result.fetchone()
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
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
                else:
                    row = cursor.fetchone()
                    return dict(zip(columns, row)) if row else None
            else:
                return cursor.fetchall() if fetch_all else cursor.fetchone()
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
        
        result = execute_query(conn, query, {"username": user}, fetch_all=False, as_dict=True)
        
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
