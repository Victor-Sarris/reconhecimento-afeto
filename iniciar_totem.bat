@echo off
title Inicializador do Totem Afeto
echo ===================================================
echo 🏥 Iniciando os sistemas do Totem Afeto...
echo ===================================================

echo [1/3] Abrindo o Servidor de Producao...
start /min start_servidor_producao.bat

:: Pequena pausa de 2 segundos apenas para dar um respiro ao Windows
timeout /t 2 /nobreak >nul

echo [2/3] Abrindo o Cliente da Camera...
start /min start_cliente_producao.bat

timeout /t 2 /nobreak >nul

echo [3/3] Abrindo a API do WhatsApp
start /min iniciar_api_whatsapp.bat

echo.
echo ✅ Todos os modulos foram iniciados em janelas separadas!
echo Voce ja pode fechar esta janela preta (o sistema continuara rodando nas outras).
timeout /t 10