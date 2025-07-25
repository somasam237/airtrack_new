# Airtrack Project

Ein System zum Tracking von Live-Flugdaten über die OpenSky Network API.

## 📁 Projektstruktur

```
Airtrack Project/
├── airtrack_main.py      # Hauptprogramm mit interaktivem Menü
├── data_processor.py     # Datenverarbeitung und Aircraft-Klasse
└── README.md            # Diese Datei
```

## 🚀 Schnellstart

### 1. Einzelne Fluganalyse
```bash
python airtrack_main.py
# Dann Option 1 wählen
```

### 2. Live-Datenabruf starten
```bash
python airtrack_main.py
# Dann Option 2-5 je nach Bedarf wählen
```

### 3. Nur die Datenverarbeitung testen
```bash
python data_processor.py
```

## 📊 Features

### ✅ Implementiert:
- **Live-Datenabruf**: Kontinuierliche Abfrage der OpenSky API
- **Datenverarbeitung**: Strukturierung der State Vectors
- **Filterung**: Nach Land, Höhe, Flugstatus, etc.
- **Statistiken**: Automatische Berechnung von Kennzahlen
- **Export**: JSON-Export für weitere Verarbeitung

### 🔄 Geplant:
- **Flug-Tracking**: Zusammenführung von Einzelpositionen zu Flugwegen
- **Aircraft Database**: Anreicherung mit Flugzeugtyp-Informationen
- **Datenbank-Speicherung**: Persistente Speicherung
- **Kartenvisualisierung**: Interaktive Karte mit Flugrouten

## 🛠 Technische Details

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

## 📋 Verwendung

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

## 📈 Beispiel-Output

```
=== FLUGANALYSE ===
Données récupérées : 11837 avions

📊 GESAMTSTATISTIKEN:
   total_aircraft: 11837
   airborne: 11062
   on_ground: 775
   with_position: 11726
   country_count: 107
   avg_altitude: 6262m

🔍 DETAILANALYSEN:
   Deutsche Flugzeuge: 260 Flugzeuge
   Hochfliegende (>10.000m): 3966 Flugzeuge
   Schnelle Flugzeuge (>800 km/h): 4123 Flugzeuge
```

## 🎯 Nächste Entwicklungsschritte

1. **Flug-Tracking implementieren**
2. **Aircraft Database integrieren**
3. **Datenbank-Backend hinzufügen**
4. **Web-Interface mit Karte erstellen**

---
*Entwickelt für Live-Flugdaten-Tracking und -Analyse*
