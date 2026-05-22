@echo off
chcp 65001 >nul
title TecOS Local v1.0

echo ============================================================
echo   TecOS Local v1.0 - Sprint 1
echo ============================================================
echo.

REM ── Verifica se Python está instalado ──────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale o Python 3.10 ou superior:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM ── Verifica/cria ambiente virtual ─────────────────────────
if not exist "venv\" (
    echo [INFO] Criando ambiente virtual Python...
    python -m venv venv
    echo [OK] Ambiente virtual criado.
    echo.
)

REM ── Ativa o ambiente virtual ────────────────────────────────
call venv\Scripts\activate.bat

REM ── Instala dependências ────────────────────────────────────
echo [INFO] Instalando dependencias...
pip install -r requirements.txt --quiet
echo [OK] Dependencias instaladas.
echo.

REM ── Inicia o sistema ────────────────────────────────────────
echo [INFO] Iniciando TecOS Local...
echo [INFO] Acesse: http://localhost:5000
echo.
echo Pressione CTRL+C para encerrar o servidor.
echo ============================================================
echo.

start "" http://localhost:5000
python app.py

pause
