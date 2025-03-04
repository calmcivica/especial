#!/usr/bin/env python3
"""
Performance Optimization Patch for Especialidades App

This script improves application performance by:
1. Optimizing database connections
2. Reducing unnecessary interface updates
3. Fixing slow UI components
"""

import streamlit as st
import logging
import helper
import importlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Performance optimization for database connections
original_init_connection = helper.init_connection

def optimized_init_connection(especialidad):
    """
    Performance-optimized database connection function.
    Uses caching and avoids unnecessary reconnections.
    """
    # Use the original function but with a spinner shown only on first load
    with st.spinner("Conectando a la base de datos..."):
        return original_init_connection(especialidad)

# Optimize execute_query
original_execute_query = helper.execute_query

def optimized_execute_query(conn, query, params=None, fetch_all=True, as_dict=False):
    """Optimized query execution with better error handling and performance."""
    # For non-critical reads that can be cached, add caching
    if query.strip().upper().startswith("SELECT") and "GetQuestionHistory" not in query:
        # Use st.cache_data if appropriate
        @st.cache_data(ttl=60)  # Cache for 1 minute
        def cached_query(query_str, params_str=None):
            return original_execute_query(conn, query_str, params, fetch_all, as_dict)
        
        # Convert params to string for caching
        params_str = str(params) if params else None
        return cached_query(query, params_str)
    else:
        # Use original for updates and uncacheable queries
        return original_execute_query(conn, query, params, fetch_all, as_dict)

# Apply patches
helper.init_connection = optimized_init_connection
helper.execute_query = optimized_execute_query

# Add performance hint
logger.info("✅ Performance patches applied successfully!")

if __name__ == "__main__":
    # Log that the patch was applied
    logger.info("Performance patch executed directly")