# 🚀 Airtrack Ubuntu VM Deployment Guide

## 📋 Übersicht
Dieses Guide erklärt, wie Sie Ihr Airtrack Flight Tracking System auf einer Ubuntu VM deployen.

## 🎯 Warum Ubuntu VM?

### Vorteile:
- **🔒 Isolation**: Saubere, isolierte Umgebung
- **🐧 Linux**: Production-ready Server-Umgebung  
- **📦 Dependencies**: Bessere Package-Verwaltung
- **🌐 Network**: Einfachere Port-Konfiguration
- **🚀 Skalierung**: Cloud-deployment ready

## 📁 Dateien in diesem Transfer-Paket:

```
airtrack_transfer/
├── 🐍 *.py                    # Alle Python-Module
├── 🗄️ create_airtrack_database.sql  # Database Schema
├── ⚙️ .env                    # Windows Config (Referenz)
├── ⚙️ .env_ubuntu             # Ubuntu Config
├── 📦 requirements.txt        # Python Dependencies
├── 🔧 ubuntu_setup.sh         # Automatisches Setup
├── 🔧 airtrack.service       # Systemd Service
├── 📁 templates/             # Web Interface
└── 📄 README.md              # Diese Anleitung
```

## 🛠️ Installation auf Ubuntu VM

### Schritt 1: Dateien übertragen
```bash
# Option A: Mit SCP (von Windows)
scp -r airtrack_transfer/ user@vm-ip:~/airtrack/

# Option B: Mit shared folder oder USB
# Kopiere airtrack_transfer/ nach /home/ubuntu/airtrack/
```

### Schritt 2: Setup ausführen
```bash
cd ~/airtrack
chmod +x ubuntu_setup.sh
./ubuntu_setup.sh
```

### Schritt 3: Database Schema importieren
```bash
# PostgreSQL Database Schema erstellen
sudo -u postgres psql -d airtrack_db -f create_airtrack_database.sql
```

### Schritt 4: Environment konfigurieren
```bash
# Ubuntu-spezifische Environment verwenden
cp .env_ubuntu .env

# Virtual Environment aktivieren
source airtrack_env/bin/activate
```

### Schritt 5: Airtrack starten
```bash
# Test-Start
python airtrack_web_server.py

# Oder als Service installieren
sudo cp airtrack.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable airtrack
sudo systemctl start airtrack
```

## 🌐 Zugriff konfigurieren

### VM Network Setup:
```bash
# Firewall Port öffnen
sudo ufw allow 5000

# Service Status prüfen
sudo systemctl status airtrack

# Logs anzeigen
journalctl -u airtrack -f
```

### Host-Zugriff:
- **VM IP finden**: `ip addr show`
- **Web Interface**: `http://VM-IP:5000`
- **Port Forwarding**: VirtualBox/VMware Network Settings

## 🔧 Troubleshooting

### PostgreSQL Probleme:
```bash
# Service Status
sudo systemctl status postgresql

# User-Berechtigungen prüfen
sudo -u postgres psql -c "\\du"

# Database Verbindung testen
psql -h localhost -U airtrack_user -d airtrack_db
```

### Python Dependencies:
```bash
# Virtual Environment aktivieren
source airtrack_env/bin/activate

# Packages neu installieren
pip install -r requirements.txt

# Python Version prüfen
python3 --version
```

### Network Probleme:
```bash
# Port prüfen
netstat -tlnp | grep 5000

# Firewall Status
sudo ufw status

# Service Logs
journalctl -u airtrack --no-pager
```

## 📊 Performance Monitoring

### System Resources:
```bash
# CPU/Memory Usage
htop

# Disk Space
df -h

# Network Connections
ss -tulpn | grep 5000
```

### Database Performance:
```bash
# Database Größe
sudo -u postgres psql -d airtrack_db -c "\\l+"

# Aktive Connections
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
```

## 🚀 Production Deployment

### Security:
```bash
# Updates installieren
sudo apt update && sudo apt upgrade

# Firewall konfigurieren
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 5000

# SSL/HTTPS Setup (Optional)
# nginx reverse proxy für HTTPS
```

### Backup:
```bash
# Database Backup
pg_dump -h localhost -U airtrack_user airtrack_db > backup.sql

# Code Backup
tar -czf airtrack_backup.tar.gz ~/airtrack/
```

## 💡 Tipps & Best Practices

1. **🔄 Auto-Start**: Service automatisch bei Boot starten
2. **📊 Monitoring**: Logs regelmäßig prüfen
3. **💾 Backups**: Regelmäßige Database-Backups
4. **🔒 Security**: Updates und Firewall-Regeln
5. **📈 Performance**: htop für Resource-Monitoring

## 📞 Support

Bei Problemen:
1. Logs prüfen: `journalctl -u airtrack -f`
2. Service Status: `sudo systemctl status airtrack`
3. Database Connection: `psql -h localhost -U airtrack_user -d airtrack_db`
4. Python Environment: `source airtrack_env/bin/activate`

---

**Happy Flight Tracking! ✈️🗺️**
