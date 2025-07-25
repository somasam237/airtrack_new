#!/bin/bash

echo "🐧 Airtrack Ubuntu VM Setup"
echo "=========================="

# System Update
echo "📦 System aktualisieren..."
sudo apt update && sudo apt upgrade -y

# Python und Dependencies
echo "🐍 Python installieren..."
sudo apt install -y python3 python3-pip python3-venv

# PostgreSQL installieren
echo "🗄️ PostgreSQL installieren..."
sudo apt install -y postgresql postgresql-contrib

# PostgreSQL konfigurieren
echo "🔧 PostgreSQL konfigurieren..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Database User erstellen
echo "👤 Database User erstellen..."
sudo -u postgres psql -c "CREATE USER airtrack_user WITH PASSWORD 'airtrack_password';"
sudo -u postgres psql -c "CREATE DATABASE airtrack_db OWNER airtrack_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE airtrack_db TO airtrack_user;"

# Virtual Environment erstellen
echo "🏠 Python Virtual Environment erstellen..."
python3 -m venv airtrack_env
source airtrack_env/bin/activate

# Python Packages installieren
echo "📦 Python Packages installieren..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Setup abgeschlossen!"
echo "🚀 Starte mit: source airtrack_env/bin/activate && python airtrack_web_server.py"
