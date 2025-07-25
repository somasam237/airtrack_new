#!/bin/bash

# 🚀 Airtrack Ubuntu VM Quick Start Script
# Dieses Script startet Airtrack nach dem Setup

echo "🚀 Airtrack Quick Start"
echo "====================="

# Virtual Environment aktivieren
if [ -f "airtrack_env/bin/activate" ]; then
    echo "🐍 Aktiviere Python Virtual Environment..."
    source airtrack_env/bin/activate
else
    echo "❌ Virtual Environment nicht gefunden!"
    echo "💡 Führe zuerst ubuntu_setup.sh aus"
    exit 1
fi

# Database Connection testen
echo "🗄️ Teste Database Verbindung..."
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        database='airtrack_db',
        user='airtrack_user',
        password='airtrack_password'
    )
    print('✅ Database Verbindung erfolgreich!')
    conn.close()
except Exception as e:
    print(f'❌ Database Fehler: {e}')
    exit(1)
"

# Environment File prüfen
if [ ! -f ".env" ]; then
    echo "⚙️ Erstelle .env aus Ubuntu Template..."
    cp .env_ubuntu .env
fi

# Web Server starten
echo "🌐 Starte Airtrack Web Server..."
echo "📍 Zugriff über: http://$(hostname -I | awk '{print $1}'):5000"
echo "🔧 Stoppen mit: Ctrl+C"
echo ""

python airtrack_web_server.py
