# Airtrack Project

Ein System zum Tracking von Live-Flugdaten über die OpenSky Network API.
<img width="1879" height="1013" alt="Capture d'écran 2025-09-14 184010" src="https://github.com/user-attachments/assets/5b43bece-5de7-4d5a-8dd9-77bb68e0271c" />

<img width="1885" height="1023" alt="Capture d'écran 2025-09-14 183657" src="https://github.com/user-attachments/assets/98a8aa87-23f6-482d-a561-6686914a8734" />

<img width="1899" height="1016" alt="Capture d'écran 2025-09-14 184247" src="https://github.com/user-attachments/assets/337060b4-a132-467f-be3e-e8f4b8708222" />

<img width="1910" height="1026" alt="Capture d'écran 2025-09-14 184137" src="https://github.com/user-attachments/assets/21ebb72c-74fa-4a8f-ad5a-e917f2ef4125" />

Projekt Übersicht


##  Projektstruktur

```
Airtrack Project/
├── airtrack_main.py      # Hauptprogramm mit interaktivem Menü
├── data_processor.py     # Datenverarbeitung und Aircraft-Klasse
└── README.md            # Diese Datei
```

##  Schnellstart

### 1. Umgebung einrichten
```bash
# 1. Repository klonen
git clone <repository-url>
cd airtrack_new

# 2. Umgebungsvariablen konfigurieren
cp .env.example .env
# Bearbeite .env und setze deine Datenbankpasswort

# 3. Abhängigkeiten installieren
pip install -r requirements.txt
```

### 2. Einzelne Fluganalyse
```bash
python airtrack_main.py
# Dann Option 1 wählen
```

### 3. Live-Datenabruf starten
```bash
python airtrack_main.py
# Dann Option 2-5 je nach Bedarf wählen
```

### 4. Nur die Datenverarbeitung testen
```bash
python data_processor.py
```

##  Features

###  Implementiert:
- **Live-Datenabruf**: Kontinuierliche Abfrage der OpenSky API
- **Datenverarbeitung**: Strukturierung der State Vectors
- **Filterung**: Nach Land, Höhe, Flugstatus, etc.
- **Statistiken**: Automatische Berechnung von Kennzahlen
- **Export**: JSON-Export für weitere Verarbeitung

###  Geplant:
- **Flug-Tracking**: Zusammenführung von Einzelpositionen zu Flugwegen
- **Aircraft Database**: Anreicherung mit Flugzeugtyp-Informationen
- **Datenbank-Speicherung**: Persistente Speicherung
- **Kartenvisualisierung**: Interaktive Karte mit Flugrouten

##  Technische Details

###  Umgebungskonfiguration:
Das Projekt verwendet Umgebungsvariablen für sensible Daten wie Datenbankpasswörter.

**Setup:**
1. Kopiere `.env.example` zu `.env`
2. Setze dein Datenbankpasswort in der `.env` Datei
3. Die `.env` Datei wird automatisch von Git ignoriert (Sicherheit)

**Beispiel `.env` Datei:**
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=airtrack_db
DB_USER=postgres
DB_PASSWORD=dein_sicheres_passwort_hier
```

**Ubuntu-spezifische Konfiguration:**
- Verwende `.env_ubuntu.example` als Vorlage für Ubuntu-Setups
- Kopiere zu `.env_ubuntu` und passe Werte an

### Datenquellen:
- **OpenSky Network API**: Live-Flugdaten (State Vectors)
- Geplant: Aircraft Database für Flugzeugtyp-Informationen

### Abhängigkeiten:
```bash
pip install requests
```

### API-Struktur:
Die OpenSky API liefert State Vectors mit folgenden Feldern:
- ICAO24, Callsign, Land, Position, Höhe, Geschwindigkeit, etc.

##  Verwendung

### Interaktives Menü:
1. **Einzelanalyse**: Aktuelle Flüge analysieren
2. **Live-Modus**: Kontinuierliche Datensammlung
3. **Mit Speicherung**: Daten in JSON-Dateien speichern
4. **Gefiltert**: Nur bestimmte Flugzeuge (z.B. deutsche)
5. **Hochfliegende**: Nur Flugzeuge über 5000m

### Programmgesteuert:
```python
from data_processor import DataProcessor
from airtrack_main import fetch_opensky_data

# Daten abrufen
data = fetch_opensky_data()

# Verarbeiten
processor = DataProcessor()
aircraft_list = processor.process_opensky_data(data)

# Filtern
german_aircraft = processor.filter_aircraft(aircraft_list, {
    'country': 'Germany',
    'only_airborne': True
})
```

##  Beispiel-Output

```
=== FLUGANALYSE ===
Données récupérées : 11837 avions

 GESAMTSTATISTIKEN:
   total_aircraft: 11837
   airborne: 11062
   on_ground: 775
   with_position: 11726
   country_count: 107
   avg_altitude: 6262m

 DETAILANALYSEN:
   Deutsche Flugzeuge: 260 Flugzeuge
   Hochfliegende (>10.000m): 3966 Flugzeuge
   Schnelle Flugzeuge (>800 km/h): 4123 Flugzeuge
```


