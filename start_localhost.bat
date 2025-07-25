@echo off
echo 🚀 Starte Airtrack Web Server auf localhost...
echo ===============================================

REM Prüfe ob Python verfügbar ist
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python nicht gefunden! Bitte installieren Sie Python.
    pause
    exit /b 1
)

REM Installiere Requirements falls nötig
echo 📦 Prüfe Python-Abhängigkeiten...
pip install -r requirements.txt >nul 2>&1

REM Starte den Server
echo 🌐 Starte Server auf http://localhost:5000
echo 🔧 Zum Stoppen: Ctrl+C drücken
echo.

python start_localhost.py

pause
