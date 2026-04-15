@echo off
title Totem Afeto - Cliente (Camera)
echo Iniciando Camera do Totem...

:: Aguarda 3 segundos para o servidor subir primeiro
timeout /t 3 /nobreak >nul

:: Entra na pasta correta onde esta a venv
cd core-reconhecimento

:start_cliente
echo [Verificacao] Iniciando cliente.py...

:: Ativa a venv e inicia o cliente
start /b /wait cmd /c "call venv\Scripts\activate && python script\cliente.py"

echo [ALERTA] A Camera/Cliente fechou! Reiniciando em 5 segundos...
timeout /t 5 /nobreak >nul
goto start_cliente