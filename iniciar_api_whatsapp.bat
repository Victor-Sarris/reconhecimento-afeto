@echo off
echo ===================================================
echo      A INICIAR SISTEMA TOTEM - INSTITUTO AFETO     
echo ===================================================

echo.
echo [1/3] A iniciar Evolution API (WhatsApp)...
start /min "API WhatsApp" cmd /k "cd api-whatsapp && npm run start:prod"