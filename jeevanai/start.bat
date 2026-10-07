@echo off
cd /d "%~dp0"
if not exist .venv (python -m venv .venv)
call .venv\Scripts\activate
pip install -r requirements.txt
if not exist .env copy .env.example .env
echo.
echo Open http://127.0.0.1:8000/ in your browser
uvicorn app.main:app --reload
pause
