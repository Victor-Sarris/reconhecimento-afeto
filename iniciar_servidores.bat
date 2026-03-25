@echo off
echo ===================================================
echo      A INICIAR SISTEMA TOTEM - INSTITUTO AFETO     
echo ===================================================

echo.
echo [1/3] A iniciar Evolution API (WhatsApp)...
start "API WhatsApp" cmd /k "cd api-whatsapp && npm run start:prod"

:: Espera 10 segundos para dar tempo do Node e do Prisma subirem o servidor
timeout /t 10 /nobreak >nul

echo.
echo [2/3] A iniciar Servidor de Reconhecimento Facial...
start "Servidor Python" cmd /k "cd core-reconhecimento && call venv\Scripts\activate && python script/servidor.py"

:: Espera 5 segundos para o servidor Flask ficar online
timeout /t 5 /nobreak >nul

echo.
echo [3/3] A abrir Interface do Totem...
start "Totem Cliente" cmd /c "cd core-reconhecimento && call venv\Scripts\activate && python script/cliente.py"

echo.
echo Todos os sistemas foram iniciados com sucesso!
pause