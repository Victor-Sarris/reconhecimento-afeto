@echo off
title Totem Afeto - Servidor
echo Iniciando Servidor...

:: Entra na pasta correta onde esta a venv
cd core-reconhecimento

:start_servidor
echo [Verificacao] Iniciando servidor.py...

:: Ativa a venv e inicia o servidor
start /b /wait cmd /c "call venv\Scripts\activate && python script\servidor.py"

echo [ALERTA] O Servidor caiu! Reiniciando em 5 segundos...
timeout /t 5 /nobreak >nul
goto start_servidor