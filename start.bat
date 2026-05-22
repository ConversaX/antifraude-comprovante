@echo off
echo ================================================
echo   Anti-Fraude de Comprovantes
echo ================================================
echo.

if not exist ".venv" (
    echo [ERRO] Ambiente virtual nao encontrado.
    echo Execute: uv venv --python 3.11 ^&^& uv pip install -r requirements.txt
    pause
    exit /b 1
)

echo [1/2] Iniciando FastAPI na porta 8000...
start "FastAPI - Anti-Fraude" cmd /k ".venv\Scripts\uvicorn.exe main:app --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak > nul

echo [2/2] Iniciando Streamlit na porta 8501...
start "Streamlit - Anti-Fraude" cmd /k ".venv\Scripts\streamlit.exe run app.py --server.port 8501"

echo.
echo Servidores iniciados:
echo   FastAPI:    http://127.0.0.1:8000/docs
echo   Streamlit:  http://localhost:8501
echo.
pause
