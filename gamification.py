import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import helper as h
import logging
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)

def display_level_progress(user_data):
    """
    Display a user's level and progress bar to the next level.
    
    Args:
        user_data (dict): User's experience data
    """
    try:
        # Get user data
        level = user_data.get("level", 1)
        xp = user_data.get("xp", 0)
        rango = user_data.get("rango", "Iniciado")
        
        # XP required for next level
        level_xp_requirements = {
            1: 100,   # 100 XP for level 1->2
            2: 200,   # 200 XP for level 2->3
            3: 400,   # 400 XP for level 3->4
            4: 800,   # 800 XP for level 4->5
            5: 1600   # 1600 XP for level 5->6
        }
        
        next_level_xp = level_xp_requirements.get(level, 3000)
        
        # Emoji mapping for ranks
        rank_emojis = {
            "Iniciado": "🤓",
            "Padawan": "🤠",
            "Maestro": "🗡️",
            "Parra": "🤖"
        }
        
        # Calculate progress percentage
        progress_pct = min(100, int((xp / next_level_xp) * 100))
        
        # Display rank and level
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown(f"<h1 style='text-align: center; font-size: 3em;'>{rank_emojis.get(rango, '🤓')}</h1>", unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"**Rango**: {rango}")
            st.markdown(f"**Nivel**: {level}")
            st.progress(progress_pct / 100)
            st.markdown(f"**XP**: {xp}/{next_level_xp} ({progress_pct}%)")
            
            if level >= 6:
                st.markdown("**¡Nivel máximo alcanzado!**")
    except Exception as e:
        logger.error(f"Error displaying level progress: {str(e)}", exc_info=True)
        st.error("Error displaying level information")

def display_streak(streak_days):
    """
    Display a user's study streak.
    
    Args:
        streak_days (int): Number of consecutive days studying
    """
    try:
        # Calculate streak emoji (flames increase with streak length)
        if streak_days >= 30:
            streak_emoji = "🔥🔥🔥"
        elif streak_days >= 7:
            streak_emoji = "🔥🔥"
        elif streak_days >= 3:
            streak_emoji = "🔥"
        else:
            streak_emoji = "📅"
            
        # Display streak
        st.markdown(f"<h3 style='text-align: center;'>{streak_emoji} {streak_days} días consecutivos {streak_emoji}</h3>", unsafe_allow_html=True)
        
        # Add motivational message based on streak
        if streak_days >= 30:
            st.markdown("**¡Increíble! Tu consistencia es admirable.**")
        elif streak_days >= 7:
            st.markdown("**¡Gran trabajo! Mantén el ritmo.**")
        elif streak_days >= 3:
            st.markdown("**¡Buen comienzo! ¿Puedes llegar a 7 días?**")
        else:
            if streak_days == 0:
                st.markdown("**Comienza tu racha hoy. ¡La consistencia es clave!**")
            else:
                st.markdown("**Sigue así. Estudiar cada día marca la diferencia.**")
    except Exception as e:
        logger.error(f"Error displaying streak: {str(e)}", exc_info=True)

def display_achievements(conn, user, is_sql=False):
    """
    Display a user's earned achievements.
    
    Args:
        conn: Database connection
        user (str): Username
        is_sql (bool): Whether this is for SQL specialization
    """
    try:
        # Get user achievements
        if is_sql:
            query = """
            SELECT a.name, a.description, a.icon, ua.earned_date
            FROM [dbo].Fact_User_Achievements ua
            JOIN [dbo].Dim_Achievements a ON ua.achievement_id = a.id
            WHERE ua.username = :username
            ORDER BY ua.earned_date DESC
            """
        else:
            query = """
            SELECT a.name, a.description, a.icon, ua.earned_date
            FROM [esnowflake].[dbo].Fact_User_Achievements ua
            JOIN [esnowflake].[dbo].Dim_Achievements a ON ua.achievement_id = a.id
            WHERE ua.user_nickname = :username
            ORDER BY ua.earned_date DESC
            """
        
        achievements = h.execute_query(conn, query, {"username": user}, as_dict=True)
        
        if not achievements:
            st.markdown("### Logros")
            st.info("¡Todavía no has conseguido ningún logro! Sigue estudiando para desbloquearlos.")
            return
            
        # Display achievements
        st.markdown("### Logros conseguidos")
        
        # Create a grid for achievements
        cols = st.columns(3)
        
        for i, achievement in enumerate(achievements):
            with cols[i % 3]:
                icon = achievement.get("icon", "🏆")
                name = achievement.get("name", "Logro")
                description = achievement.get("description", "")
                earned_date = achievement.get("earned_date")
                
                if earned_date:
                    earned_str = earned_date.strftime("%d/%m/%Y")
                else:
                    earned_str = "Fecha desconocida"
                    
                st.markdown(f"#### {icon} {name}")
                st.markdown(f"{description}")
                st.markdown(f"*Conseguido: {earned_str}*")
                st.markdown("---")
                
        # Available achievements
        if is_sql:
            query = """
            SELECT a.name, a.description, a.icon
            FROM [dbo].Dim_Achievements a
            WHERE NOT EXISTS (
                SELECT 1 FROM [dbo].Fact_User_Achievements ua 
                WHERE ua.achievement_id = a.id AND ua.username = :username
            )
            """
        else:
            query = """
            SELECT a.name, a.description, a.icon
            FROM [esnowflake].[dbo].Dim_Achievements a
            WHERE NOT EXISTS (
                SELECT 1 FROM [esnowflake].[dbo].Fact_User_Achievements ua 
                WHERE ua.achievement_id = a.id AND ua.user_nickname = :username
            )
            """
        
        available_achievements = h.execute_query(conn, query, {"username": user}, as_dict=True)
        
        if available_achievements:
            st.markdown("### Logros disponibles")
            
            # Create a grid for available achievements
            cols = st.columns(3)
            
            for i, achievement in enumerate(available_achievements):
                with cols[i % 3]:
                    icon = achievement.get("icon", "🔒")
                    name = achievement.get("name", "Logro")
                    description = achievement.get("description", "")
                    
                    st.markdown(f"#### {icon} {name}")
                    st.markdown(f"{description}")
                    st.markdown("*Por conseguir*")
                    st.markdown("---")
    except Exception as e:
        logger.error(f"Error displaying achievements: {str(e)}", exc_info=True)
        st.error("Error displaying achievements")

def display_xp_history(conn, user, is_sql=False):
    """
    Display a user's XP gain history as a chart.
    
    Args:
        conn: Database connection
        user (str): Username
        is_sql (bool): Whether this is for SQL specialization
    """
    try:
        # Get XP history over the last 30 days
        if is_sql:
            query = """
            SELECT 
                CONVERT(DATE, timestamp) as date,
                SUM(xp_amount) as daily_xp
            FROM [dbo].Fact_XP_History
            WHERE username = :username
            AND timestamp >= DATEADD(day, -30, GETDATE())
            GROUP BY CONVERT(DATE, timestamp)
            ORDER BY date
            """
        else:
            query = """
            SELECT 
                CONVERT(DATE, timestamp) as date,
                SUM(xp_amount) as daily_xp
            FROM [esnowflake].[dbo].Fact_XP_History
            WHERE user_nickname = :username
            AND timestamp >= DATEADD(day, -30, GETDATE())
            GROUP BY CONVERT(DATE, timestamp)
            ORDER BY date
            """
        
        xp_history = h.execute_query(conn, query, {"username": user}, as_dict=True)
        
        if not xp_history:
            st.markdown("### Historial de XP")
            st.info("No hay datos de XP recientes. ¡Comienza a estudiar para ganar XP!")
            return
            
        # Convert to DataFrame
        df = pd.DataFrame(xp_history)
        
        # Fill in missing dates with 0 XP
        date_range = pd.date_range(
            start=(datetime.now() - timedelta(days=30)).date(),
            end=datetime.now().date()
        )
        date_df = pd.DataFrame({'date': date_range})
        df = pd.merge(date_df, df, on='date', how='left').fillna(0)
        
        # Create the chart
        fig = px.bar(
            df, 
            x='date', 
            y='daily_xp',
            labels={'date': 'Fecha', 'daily_xp': 'XP diario'},
            title='XP ganado en los últimos 30 días'
        )
        
        # Set color based on XP amount
        fig.update_traces(marker_color=df['daily_xp'].apply(
            lambda x: 'lightblue' if x < 20 else ('royalblue' if x < 50 else 'darkblue')
        ))
        
        # Update layout
        fig.update_layout(
            xaxis_title="Fecha",
            yaxis_title="XP ganado",
            showlegend=False
        )
        
        # Display chart
        st.plotly_chart(fig, use_container_width=True)
        
        # Display total XP gained
        total_xp = df['daily_xp'].sum()
        st.markdown(f"**Total de XP ganado en los últimos 30 días**: {int(total_xp)} XP")
    except Exception as e:
        logger.error(f"Error displaying XP history: {str(e)}", exc_info=True)
        st.error("Error displaying XP history")

def display_leaderboard(conn, is_sql=False):
    """
    Display a leaderboard of top users.
    
    Args:
        conn: Database connection
        is_sql (bool): Whether this is for SQL specialization
    """
    try:
        # Get top 10 users by XP
        if is_sql:
            query = """
            SELECT 
                username,
                level,
                xp,
                streak_days
            FROM [dbo].Dim_Users
            ORDER BY level DESC, xp DESC
            OFFSET 0 ROWS FETCH NEXT 10 ROWS ONLY
            """
            name_field = "username"
        else:
            query = """
            SELECT 
                name as username,
                level,
                xp,
                rango,
                streak_days
            FROM [esnowflake].[dbo].Dim_Users
            ORDER BY level DESC, xp DESC
            OFFSET 0 ROWS FETCH NEXT 10 ROWS ONLY
            """
            name_field = "username"
        
        leaderboard = h.execute_query(conn, query, as_dict=True)
        
        if not leaderboard:
            st.markdown("### Clasificación")
            st.info("No hay datos de usuarios disponibles.")
            return
            
        # Convert to DataFrame
        df = pd.DataFrame(leaderboard)
        
        # Add rank column
        df.insert(0, 'Posición', range(1, len(df) + 1))
        
        # Rename columns for display
        column_map = {
            "username": "Usuario",
            "level": "Nivel",
            "xp": "XP",
            "rango": "Rango",
            "streak_days": "Racha"
        }
        df = df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})
        
        # Display leaderboard
        st.markdown("### Clasificación")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Add note about leaderboard
        st.markdown("*La clasificación se actualiza diariamente basada en nivel y XP.*")
    except Exception as e:
        logger.error(f"Error displaying leaderboard: {str(e)}", exc_info=True)
        st.error("Error displaying leaderboard")

def gamification_tab(conn, user, is_sql=False):
    """
    Display the gamification tab with all components.
    
    Args:
        conn: Database connection
        user (str): Username
        is_sql (bool): Whether this is for SQL specialization
    """
    try:
        st.markdown("## Sistema de Gamificación")
        
        if not user:
            st.warning("Por favor, selecciona un usuario para ver tu progreso y gamificación.")
            return
            
        # Get user data
        user_data = h.get_user_experience(conn, user, is_sql)
        
        # User information section
        st.markdown("### Tu perfil")
        
        col1, col2 = st.columns([2, 3])
        
        with col1:
            # Display level progress
            display_level_progress(user_data)
            
            # Update streak
            streak_days, is_new_streak = h.update_streak(conn, user, is_sql)
            
            # Display streak
            display_streak(streak_days)
            
            # Show streak notification if it's a new day
            if is_new_streak:
                st.success(f"¡Has aumentado tu racha a {streak_days} días consecutivos! +5 XP")
                
                # Award XP for maintaining streak
                h.add_experience(
                    conn, 
                    user, 
                    5, 
                    f"Mantener racha de {streak_days} días", 
                    is_sql
                )
                
                # Check for streak achievements
                if streak_days == 3:
                    award_achievement(conn, user, "3-Day Streak", is_sql)
                elif streak_days == 7:
                    award_achievement(conn, user, "7-Day Streak", is_sql)
                elif streak_days == 30:
                    award_achievement(conn, user, "30-Day Streak", is_sql)
        
        with col2:
            # Display XP history
            display_xp_history(conn, user, is_sql)
        
        # Display achievements
        display_achievements(conn, user, is_sql)
        
        # Display leaderboard
        display_leaderboard(conn, is_sql)
    except Exception as e:
        logger.error(f"Error in gamification tab: {str(e)}", exc_info=True)
        st.error("Error displaying gamification information")

def award_achievement(conn, user, achievement_name, is_sql=False):
    """
    Award an achievement to a user if they don't already have it.
    
    Args:
        conn: Database connection
        user (str): Username
        achievement_name (str): Name of the achievement to award
        is_sql (bool): Whether this is for SQL specialization
        
    Returns:
        bool: Whether the achievement was awarded
    """
    try:
        # Check if user already has this achievement
        if is_sql:
            query = """
            SELECT COUNT(*) as count
            FROM [dbo].Fact_User_Achievements ua
            JOIN [dbo].Dim_Achievements a ON ua.achievement_id = a.id
            WHERE ua.username = :username AND a.name = :achievement_name
            """
        else:
            query = """
            SELECT COUNT(*) as count
            FROM [esnowflake].[dbo].Fact_User_Achievements ua
            JOIN [esnowflake].[dbo].Dim_Achievements a ON ua.achievement_id = a.id
            WHERE ua.user_nickname = :username AND a.name = :achievement_name
            """
        
        result = h.execute_query(
            conn, 
            query, 
            {"username": user, "achievement_name": achievement_name}, 
            fetch_all=False,
            as_dict=True
        )
        
        if result and result.get("count", 0) > 0:
            return False  # User already has this achievement
            
        # Get achievement details
        if is_sql:
            query = """
            SELECT id, xp_reward
            FROM [dbo].Dim_Achievements
            WHERE name = :achievement_name
            """
        else:
            query = """
            SELECT id, xp_reward
            FROM [esnowflake].[dbo].Dim_Achievements
            WHERE name = :achievement_name
            """
        
        achievement = h.execute_query(
            conn, 
            query, 
            {"achievement_name": achievement_name}, 
            fetch_all=False,
            as_dict=True
        )
        
        if not achievement:
            return False  # Achievement not found
            
        # Award the achievement
        achievement_id = achievement.get("id")
        xp_reward = achievement.get("xp_reward", 0)
        
        if is_sql:
            query = """
            INSERT INTO [dbo].Fact_User_Achievements (username, achievement_id, earned_date)
            VALUES (:username, :achievement_id, CURRENT_TIMESTAMP)
            """
        else:
            query = """
            INSERT INTO [esnowflake].[dbo].Fact_User_Achievements (user_nickname, achievement_id, earned_date)
            VALUES (:username, :achievement_id, CURRENT_TIMESTAMP)
            """
        
        h.execute_non_query(conn, query, {"username": user, "achievement_id": achievement_id})
        
        # Award XP for the achievement
        if xp_reward > 0:
            h.add_experience(
                conn, 
                user, 
                xp_reward, 
                f"Logro: {achievement_name}", 
                is_sql
            )
            
        # Show success message
        st.success(f"¡Has conseguido el logro **{achievement_name}**! +{xp_reward} XP")
        
        return True
    except Exception as e:
        logger.error(f"Error awarding achievement: {str(e)}", exc_info=True)
        return False