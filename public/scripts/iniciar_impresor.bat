@echo off
chcp 65001 >nul
title San Parrilla POS - Agente de Impresion Automatica (SAT Q22)

echo ============================================================
echo      RESTAURANTE SAN PARRILLA - IMPRESION AUTOMATICA
echo ============================================================
echo  Este programa escucha los pedidos que entran desde los
echo  celulares (meseros, cajeros, admin, web) y los imprime
echo  de inmediato en la impresora termica SAT Q22 (80mm).
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

rem 3. Configurar auto-inicio permanente en Windows (shell:startup)
echo [*] Configurando auto-inicio permanente con Windows...
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
if exist "%STARTUP_FOLDER%" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%STARTUP_FOLDER%\SanParrillaImpresor.lnk'); $s.TargetPath = '%~f0'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'San Parrilla POS Impresor Automatico'; $s.Save()" >nul 2>&1
    echo [OK] Auto-inicio configurado: Se iniciara solo cada vez que se prenda el PC.
)

rem 4. Instalar dependencias si no estan presentes
echo [*] Verificando dependencias necesarias (requests, pywin32)...
python -m pip install --quiet requests pywin32 >nul 2>&1

echo [*] Iniciando agente de impresion para SAT Q22...
echo.
echo ============================================================
echo  LISTO: El agente de impresion ya esta activo y funcionando.
echo  NO TIENES QUE HACER NADA MAS.
echo  Cada vez que se prenda el computador arrancara solo.
echo ============================================================
echo.

python print_agent.py

if %errorlevel% neq 0 (
    echo.
    echo [!] El agente de impresion se ha detenido con codigo de error %errorlevel%.
    pause
)
