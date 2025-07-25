@echo off
REM SSH Tunnel Setup für Airtrack VM Access (Windows)
REM Dieses Script erstellt einen SSH-Tunnel zur Ubuntu VM

echo 🔗 SSH Tunnel Setup für Airtrack
echo ==================================

REM VM Verbindungsdaten (anpassen!)
set VM_USER=your-username
set VM_HOST=your-vm-ip
set VM_PORT=22
set LOCAL_PORT=5000
set REMOTE_PORT=5000

echo 📋 Konfiguration:
echo    VM Benutzer: %VM_USER%
echo    VM Host: %VM_HOST%
echo    SSH Port: %VM_PORT%
echo    Local Port: %LOCAL_PORT%
echo    Remote Port: %REMOTE_PORT%
echo.

echo 🔗 Erstelle SSH Tunnel...
echo    Kommando: ssh -L %LOCAL_PORT%:localhost:%REMOTE_PORT% -N %VM_USER%@%VM_HOST%
echo.
echo ⚡ Nach dem Start können Sie zugreifen auf:
echo    http://localhost:%LOCAL_PORT%
echo.
echo 🛑 Zum Beenden: Ctrl+C
echo.

REM SSH Tunnel starten
ssh -L %LOCAL_PORT%:localhost:%REMOTE_PORT% -N %VM_USER%@%VM_HOST%
