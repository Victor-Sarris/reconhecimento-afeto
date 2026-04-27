@echo off
title Conectar WhatsApp - Totem Afeto
color 0B

echo ===================================================
echo      GERADOR DE QR CODE - WHATSAPP DO TOTEM
echo ===================================================
echo.
echo Iniciando a comunicacao com a API...
echo.

:: Navega ate a pasta onde o script Python esta localizado
cd core-reconhecimento\script

:: Executa o script de conexao
python conectar_whatsapp.py

echo.
echo ===================================================
echo Pressione qualquer tecla para fechar esta janela...
pause >nul