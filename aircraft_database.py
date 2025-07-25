import csv
import json
import requests
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class AircraftInfo:
    """
    Repräsentiert zusätzliche Informationen über ein Flugzeug.
    Diese Daten kommen aus der Aircraft Database und reichern die Live-Daten an.
    """
    icao24: str
    registration: Optional[str] = None  
    aircraft_type: Optional[str] = None  
    manufacturer: Optional[str] = None  
    model: Optional[str] = None  
    airline: Optional[str] = None  
    airline_iata: Optional[str] = None  
    airline_icao: Optional[str] = None  
    owner: Optional[str] = None  
    operator: Optional[str] = None  
    construction_number: Optional[str] = None  
    first_flight: Optional[str] = None  
    engines: Optional[str] = None  
    seats: Optional[int] = None  
    category: Optional[str] = None  
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary für JSON-Export."""
        return {
            'icao24': self.icao24,
            'registration': self.registration,
            'aircraft_type': self.aircraft_type,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'airline': self.airline,
            'airline_iata': self.airline_iata,
            'airline_icao': self.airline_icao,
            'owner': self.owner,
            'operator': self.operator,
            'construction_number': self.construction_number,
            'first_flight': self.first_flight,
            'engines': self.engines,
            'seats': self.seats,
            'category': self.category
        }

class AircraftDatabase:
    """
    Verwaltet eine Datenbank mit Flugzeuginformationen für die Datenanreicherung.
    
    Unterstützt mehrere Datenquellen:
    1. Lokale CSV-Dateien
    2. Online APIs (OpenSky Network)
    3. Cache für Performance
    """
    
    def __init__(self):
        self.aircraft_cache: Dict[str, AircraftInfo] = {}  # icao24 -> AircraftInfo
        self.cache_hits = 0
        self.cache_misses = 0
        self.api_calls = 0
        self.csv_loaded_count = 0
        
        print("🛩 Aircraft Database initialisiert")
        print("   Verfügbare Datenquellen:")
        print("   1. CSV-Dateien (lokal)")
        print("   2. OpenSky Network API")
        print("   3. Memory Cache")
    
    def load_csv_database(self, csv_file_path: str) -> int:
        """
        Lädt Flugzeugdaten aus einer CSV-Datei.
        
        Erwartetes CSV-Format:
        icao24,registration,aircraft_type,manufacturer,model,airline,airline_iata,airline_icao
        
        Args:
            csv_file_path: Pfad zur CSV-Datei
            
        Returns:
            Anzahl geladener Datensätze
        """
        print(f"📂 Lade Aircraft Database aus CSV: {csv_file_path}")
        
        if not Path(csv_file_path).exists():
            print(f"❌ CSV-Datei nicht gefunden: {csv_file_path}")
            return 0
        
        loaded_count = 0
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    icao24 = row.get('icao24', '').strip().lower()
                    if not icao24:
                        continue
                    
                    aircraft_info = AircraftInfo(
                        icao24=icao24,
                        registration=row.get('registration') or None,
                        aircraft_type=row.get('aircraft_type') or row.get('type') or None,
                        manufacturer=row.get('manufacturer') or None,
                        model=row.get('model') or None,
                        airline=row.get('airline') or row.get('operator') or None,
                        airline_iata=row.get('airline_iata') or None,
                        airline_icao=row.get('airline_icao') or None,
                        owner=row.get('owner') or None,
                        operator=row.get('operator') or None,
                        construction_number=row.get('construction_number') or row.get('cn') or None,
                        first_flight=row.get('first_flight') or None,
                        engines=row.get('engines') or None,
                        seats=int(row.get('seats', 0)) if row.get('seats', '').isdigit() else None,
                        category=row.get('category') or None
                    )
                    
                    self.aircraft_cache[icao24] = aircraft_info
                    loaded_count += 1
                
                self.csv_loaded_count = loaded_count
                print(f"✅ {loaded_count} Flugzeuge aus CSV geladen")
                return loaded_count
                
        except Exception as e:
            print(f"❌ Fehler beim Laden der CSV-Datei: {e}")
            return 0
    
    def get_aircraft_info(self, icao24: str, use_api: bool = True) -> Optional[AircraftInfo]:
        """
        Ruft Flugzeuginformationen für eine ICAO24-Adresse ab.
        
        Reihenfolge der Datenquellen:
        1. Memory Cache (schnellste)
        2. OpenSky Network API (falls use_api=True)
        3. Fallback zu None
        
        Args:
            icao24: ICAO24-Adresse des Flugzeugs
            use_api: Ob API verwendet werden soll bei Cache-Miss
            
        Returns:
            AircraftInfo-Objekt oder None
        """
        icao24 = icao24.strip().lower()
        
        # 1. Cache prüfen
        if icao24 in self.aircraft_cache:
            self.cache_hits += 1
            return self.aircraft_cache[icao24]
        
        self.cache_misses += 1
        
        # 2. API abfragen (falls aktiviert)
        if use_api:
            aircraft_info = self._fetch_from_opensky_api(icao24)
            if aircraft_info:
                # In Cache speichern für zukünftige Abfragen
                self.aircraft_cache[icao24] = aircraft_info
                return aircraft_info
        
        # 3. Fallback: Leeres AircraftInfo erstellen
        fallback_info = AircraftInfo(icao24=icao24)
        self.aircraft_cache[icao24] = fallback_info
        return fallback_info
    
    def _fetch_from_opensky_api(self, icao24: str) -> Optional[AircraftInfo]:
        """
        Fragt die OpenSky Network API nach Flugzeuginformationen ab.
        
        API Endpoint: https://opensky-network.org/api/metadata/aircraft/icao/{icao24}
        
        Args:
            icao24: ICAO24-Adresse
            
        Returns:
            AircraftInfo-Objekt oder None bei Fehlern
        """
        try:
            self.api_calls += 1
            url = f"https://opensky-network.org/api/metadata/aircraft/icao/{icao24}"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                aircraft_info = AircraftInfo(
                    icao24=icao24,
                    registration=data.get('registration'),
                    aircraft_type=data.get('model'),
                    manufacturer=data.get('manufacturerName'),
                    model=data.get('model'),
                    owner=data.get('owner'),
                    operator=data.get('operator'),
                    category=self._classify_aircraft_category(data.get('model', ''))
                )
                
                print(f"🌐 API: Flugzeugdaten für {icao24} abgerufen")
                return aircraft_info
            
            elif response.status_code == 404:
                # Flugzeug nicht in OpenSky Datenbank
                return None
            else:
                print(f"⚠️ API Fehler {response.status_code} für {icao24}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"API Abfrage fehlgeschlagen für {icao24}: {e}")
            return None
        except Exception as e:
            print(f"Unerwarteter Fehler bei API-Abfrage für {icao24}: {e}")
            return None
    
    def _classify_aircraft_category(self, model: str) -> str:
        """
        Klassifiziert Flugzeuge basierend auf dem Modell.
        
        Args:
            model: Flugzeugmodell
            
        Returns:
            Kategorie-String
        """
        if not model:
            return "Unknown"
        
        model_lower = model.lower()
        
        # Commercial Airlines
        commercial_indicators = ['boeing', 'airbus', 'a320', 'a330', 'a340', 'a350', 'a380', 
                               'b737', 'b747', 'b767', 'b777', 'b787', '737', '747', '767', 
                               '777', '787', 'embraer', 'crj', 'dash']
        
        # Private/Business Jets
        business_indicators = ['citation', 'gulfstream', 'lear', 'falcon', 'challenger', 
                             'global', 'phenom', 'legacy']
        
        # General Aviation
        ga_indicators = ['cessna', 'piper', 'beechcraft', 'cirrus', 'diamond', 'mooney']
        
        # Military
        military_indicators = ['f-', 'c-130', 'blackhawk', 'apache', 'chinook']
        
        for indicator in commercial_indicators:
            if indicator in model_lower:
                return "Commercial"
        
        for indicator in business_indicators:
            if indicator in model_lower:
                return "Business"
        
        for indicator in ga_indicators:
            if indicator in model_lower:
                return "General Aviation"
        
        for indicator in military_indicators:
            if indicator in model_lower:
                return "Military"
        
        return "Other"
    
    def enrich_aircraft_list(self, aircraft_list: List[Any], 
                            use_api: bool = False) -> List[Dict[str, Any]]:
        """
        Reichert eine Liste von Aircraft-Objekten mit Zusatzinformationen an.
        
        Args:
            aircraft_list: Liste von Aircraft-Objekten
            use_api: Ob API für unbekannte Flugzeuge verwendet werden soll
            
        Returns:
            Liste von angereicherten Dictionaries
        """
        enriched_aircraft = []
        processed_count = 0
        enriched_count = 0
        
        print(f"🔍 Reichere {len(aircraft_list)} Flugzeuge mit Zusatzinformationen an...")
        if use_api:
            print("   (API-Abfragen aktiviert - kann langsamer sein)")
        
        for aircraft in aircraft_list:
            processed_count += 1
            
            # Basis-Flugzeugdaten
            enriched_data = {
                'icao24': aircraft.icao24,
                'callsign': aircraft.callsign,
                'origin_country': aircraft.origin_country,
                'latitude': aircraft.latitude,
                'longitude': aircraft.longitude,
                'altitude': aircraft.baro_altitude,
                'velocity': aircraft.velocity,
                'true_track': aircraft.true_track,
                'on_ground': aircraft.on_ground,
                'fetch_time': aircraft.fetch_time
            }
            
            # Zusatzinformationen abrufen
            aircraft_info = self.get_aircraft_info(aircraft.icao24, use_api=use_api)
            if aircraft_info and (aircraft_info.aircraft_type or aircraft_info.registration):
                enriched_data.update(aircraft_info.to_dict())
                enriched_count += 1
            
            enriched_aircraft.append(enriched_data)
            
            # Progress-Update alle 1000 Flugzeuge
            if processed_count % 1000 == 0:
                print(f"   Verarbeitet: {processed_count}/{len(aircraft_list)}")
        
        print(f"✅ Anreicherung abgeschlossen:")
        print(f"   Verarbeitet: {processed_count} Flugzeuge")
        print(f"   Angereichert: {enriched_count} Flugzeuge")
        print(f"   Cache Hits: {self.cache_hits}")
        print(f"   Cache Misses: {self.cache_misses}")
        print(f"   API Calls: {self.api_calls}")
        
        return enriched_aircraft
    
    def get_statistics(self) -> Dict[str, Any]:
        """Gibt Statistiken über die Aircraft Database zurück."""
        
        # Kategorien zählen
        categories = {}
        manufacturers = {}
        for aircraft_info in self.aircraft_cache.values():
            if aircraft_info.category:
                categories[aircraft_info.category] = categories.get(aircraft_info.category, 0) + 1
            if aircraft_info.manufacturer:
                manufacturers[aircraft_info.manufacturer] = manufacturers.get(aircraft_info.manufacturer, 0) + 1
        
        return {
            'total_aircraft_in_cache': len(self.aircraft_cache),
            'csv_loaded_count': self.csv_loaded_count,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'api_calls': self.api_calls,
            'categories': categories,
            'top_manufacturers': dict(sorted(manufacturers.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def export_cache_to_csv(self, filename: str = None) -> str:
        """
        Exportiert den aktuellen Cache als CSV-Datei.
        
        Args:
            filename: Dateiname (optional)
            
        Returns:
            Verwendeter Dateiname
        """
        if not filename:
            from datetime import datetime
            filename = f"aircraft_database_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        fieldnames = ['icao24', 'registration', 'aircraft_type', 'manufacturer', 'model', 
                     'airline', 'airline_iata', 'airline_icao', 'owner', 'operator', 
                     'construction_number', 'first_flight', 'engines', 'seats', 'category']
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for aircraft_info in self.aircraft_cache.values():
                writer.writerow(aircraft_info.to_dict())
        
        print(f"💾 Aircraft Database exportiert: {filename}")
        return filename

def create_sample_aircraft_database():
    """
    Erstellt eine Beispiel-Aircraft-Database für Testzwecke.
    """
    print("🛠 Erstelle Beispiel Aircraft Database...")
    
    sample_data = [
        {
            'icao24': '4b1814',
            'registration': 'HB-JNA',
            'aircraft_type': 'Airbus A320-214',
            'manufacturer': 'Airbus',
            'model': 'A320-214',
            'airline': 'Swiss International Air Lines',
            'airline_iata': 'LX',
            'airline_icao': 'SWR',
            'category': 'Commercial'
        },
        {
            'icao24': '3c6444',
            'registration': 'D-AIQD',
            'aircraft_type': 'Airbus A320-211',
            'manufacturer': 'Airbus',
            'model': 'A320-211',
            'airline': 'Lufthansa',
            'airline_iata': 'LH',
            'airline_icao': 'DLH',
            'category': 'Commercial'
        },
        {
            'icao24': 'a12345',
            'registration': 'N123AB',
            'aircraft_type': 'Boeing 737-800',
            'manufacturer': 'Boeing',
            'model': '737-800',
            'airline': 'American Airlines',
            'airline_iata': 'AA',
            'airline_icao': 'AAL',
            'category': 'Commercial'
        },
        {
            'icao24': 'a98765',
            'registration': 'N987XY',
            'aircraft_type': 'Cessna 172',
            'manufacturer': 'Cessna',
            'model': '172',
            'owner': 'Private Owner',
            'category': 'General Aviation'
        }
    ]
    
    filename = 'sample_aircraft_database.csv'
    fieldnames = ['icao24', 'registration', 'aircraft_type', 'manufacturer', 'model', 
                 'airline', 'airline_iata', 'airline_icao', 'owner', 'operator', 
                 'construction_number', 'first_flight', 'engines', 'seats', 'category']
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for aircraft in sample_data:
            writer.writerow(aircraft)
    
    print(f"✅ Beispiel-Database erstellt: {filename}")
    return filename

def demo_aircraft_database():
    """Demonstriert die Aircraft Database Funktionalität."""
    print("=== AIRCRAFT DATABASE DEMO ===")
    
    # 1. Database initialisieren
    db = AircraftDatabase()
    
    # 2. Beispiel-Database erstellen und laden
    sample_file = create_sample_aircraft_database()
    db.load_csv_database(sample_file)
    
    # 3. Einzelne Abfragen testen
    print("\n🔍 TESTE EINZELNE ABFRAGEN:")
    test_icaos = ['4b1814', '3c6444', 'unknown123']
    
    for icao in test_icaos:
        info = db.get_aircraft_info(icao, use_api=False)  # Ohne API für Demo
        if info and info.aircraft_type:
            print(f"   {icao}: {info.aircraft_type} ({info.airline or 'N/A'})")
        else:
            print(f"   {icao}: Keine Daten verfügbar")
    
    # 4. Statistiken anzeigen
    print("\n📊 DATABASE STATISTIKEN:")
    stats = db.get_statistics()
    for key, value in stats.items():
        if key != 'categories' and key != 'top_manufacturers':
            print(f"   {key}: {value}")
    
    if stats['categories']:
        print(f"   Kategorien: {stats['categories']}")
    
    return db

if __name__ == "__main__":
    demo_aircraft_database()
