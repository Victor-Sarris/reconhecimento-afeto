@echo off
echo ===================================================
echo 🛑 Desligando o Totem Afeto...
echo ===================================================

:: Procura as janelas ocultas pelo título que demos a elas e fecha a arvore de processos
taskkill /FI "WINDOWTITLE eq Totem Afeto*" /T /F

echo.
echo ✅ O Totem foi desligado com sucesso! Pode desligar o computador.
timeout /t 5