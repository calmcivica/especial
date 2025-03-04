# CLAUDE.md - Coding Guidelines for Especialidades App

## Environment Setup
- Create venv: `python -m venv env`
- Activate venv: `.\env\Scripts\activate` (Windows)
- Install packages: `pip install -r requirements.txt`

## Running the App
- Launch app: `streamlit run especialidades.py`
- Docker build: `docker build -t especialidades-app .`
- Docker run: `docker run -p 8501:8501 especialidades-app`

## Code Style
- Type hints required for functions and class methods
- Use PEP 8 formatting (4 spaces for indentation)
- Imports order: standard library, third-party, local modules
- Error handling with try/except blocks and logger
- Use f-strings for string formatting
- Docstrings for classes and functions (use """triple quotes""")

## Naming Conventions
- Variables, functions: snake_case
- Classes: PascalCase
- Constants: UPPER_SNAKE_CASE

## Development Guidelines
- Create new branches for changes, don't modify main directly
- Log errors and important events using the logger
- Streamlit components for UI development