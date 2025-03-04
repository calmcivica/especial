# CLAUDE.md - Coding Guidelines for Especialidades App

## Environment Setup
- Create venv: `python -m venv env`
- Activate venv: `.\env\Scripts\activate` (Windows) or `source env/bin/activate` (Linux/Mac)
- Install packages: `pip install -r requirements.txt`
- Create .env file with required secrets (see .env.example)

## Running the App
- Launch app: `streamlit run especialidades.py`
- Debug mode: `streamlit run especialidades.py --logger.level=debug`
- Docker build: `docker build -t especialidades-app .`
- Docker run: `docker run -p 8501:8501 especialidades-app`

## Database Setup
- Run SQL migrations: `python -m sql_updates.py`
- Test DB connection: `python -c "import helper as h; conn = h.init_connection('sql'); print('Connected!')" `

## Code Style
- Type hints required for functions and class methods
- Use PEP 8 formatting (4 spaces for indentation)
- Imports order: standard library, third-party, local modules
- Error handling with try/except blocks and logger
- Use f-strings for string formatting
- Docstrings for classes and functions (use """triple quotes""")
- Use SQLAlchemy with parameterized queries to prevent SQL injection

## Naming Conventions
- Variables, functions: snake_case
- Classes: PascalCase
- Constants: UPPER_SNAKE_CASE
- Database columns: snake_case

## Development Guidelines
- Create new branches for changes, don't modify main directly
- Log errors and important events using the logger
- Use helper.execute_query() and helper.execute_non_query() for database operations
- Use gamification.add_experience() to award XP to users
- Streamlit components for UI development
- Update requirements.txt when adding new dependencies

## Common Issues
- Missing ODBC drivers: Install Microsoft ODBC Driver 17 for SQL Server
- Connection pooling: Check for connection leaks in exception handlers
- Pinecone API: Use API keys from environment variables (.env file)
- Helper functions: Import gamification module after helper to avoid circular dependencies