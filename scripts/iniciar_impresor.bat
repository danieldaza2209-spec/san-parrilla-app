@echo off
chcp 65001 >nul
title San Parrilla POS - Agente de Impresion Automatica (SAT Q22)

echo ============================================================
echo      RESTAURANTE SAN PARRILLA - IMPRESION AUTOMATICA
echo ============================================================
echo  Este programa escucha en tiempo real los pedidos creados
echo  desde cualquier celular, tablet o PC y los imprime de
echo  inmediato en la impresora termica SAT Q22 (80mm).
echo ============================================================
echo.

rem 1. Verificar si Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH del sistema.
    echo Por favor instala Python 3 desde https://www.python.org/downloads/
    echo y asegurate de marcar la casilla "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

rem 2. Ir a la carpeta donde reside este script
cd /d "%~dp0"

rem 3. Verificar e instalar automaticamente requests y pywin32
echo [*] Verificando e instalando librerias (requests y pywin32)...
pip install requests pywin32 --quiet >nul 2>&1
python -m pip install --quiet requests pywin32 >nul 2>&1
echo [OK] Librerias verificadas correctamente.
echo.

rem 4. Configurar auto-inicio en Windows (shell:startup) e instrucciones claras
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
if exist "%STARTUP_FOLDER%" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%STARTUP_FOLDER%\SanParrillaImpresor.lnk'); $s.TargetPath = '%~f0'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'San Parrilla POS Impresor Automatico SAT Q22'; $s.Save()" >nul 2>&1
)

echo ============================================================
echo  COMO INICIAR AUTOMATICAMENTE AL ENCENDER WINDOWS:
echo  1. Presiona las teclas Windows + R en tu teclado.
echo  2. Escribe: shell:startup y presiona Enter.
echo  3. Copia un acceso directo de iniciar_impresora.bat dentro
echo     de esa carpeta (ya se intento crear automaticamente).
echo ============================================================
echo.

:loop
echo [%time%] Iniciando Agente de Impresion SAT Q22 (print_agent.py)...
python print_agent.py
echo.
echo [!] El agente se detuvo inesperadamente. Reiniciando automaticamente en 3 segundos...
timeout /t 3 /nobreak >nul
goto loop
