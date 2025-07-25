import json
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class Aircraft:
    """
    Repräsentiert ein Flugzeug mit allen verfügbaren Daten aus dem OpenSky State Vector.
    """
    icao24: str
    callsign: Optional[str] = None
    origin_country: Optional[str] = None
    time_position: Optional[float] = None
    last_contact: Optional[float] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    baro_altitude: Optional[float] = None
    on_ground: Optional[bool] = None
    velocity: Optional[float] = None
    true_track: Optional[float] = None
    vertical_rate: Optional[float] = None
    sensors: Optional[List[int]] = None
    geo_altitude: Optional[float] = None
    squawk: Optional[str] = None
    spi: Optional[bool] = None
    position_source: Optional[int] = None
    
    # Zusätzliche Felder für unser System
    fetch_time: Optional[str] = None
    
    def has_position(self) -> bool:
        """Prüft, ob das Flugzeug eine gültige Position hat."""
        return self.latitude is not None and self.longitude is not None
    
    def is_airborne(self) -> bool:
        """Prüft, ob das Flugzeug in der Luft ist."""
        return not (self.on_ground or False)
    
    def get_speed_kmh(self) -> Optional[float]:
        """Konvertiert Geschwindigkeit von m/s zu km/h."""
        if self.velocity is not None:
            return self.velocity * 3.6
        return None
    
    def get_altitude_feet(self) -> Optional[float]:
        """Konvertiert Höhe von Metern zu Fuß."""
        if self.baro_altitude is not None:
            return self.baro_altitude * 3.28084
        return None

class DataProcessor:
    """Verarbeitet und strukturiert OpenSky API Daten."""
    
    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
    
    def parse_state_vector(self, state: List[Any]) -> Optional[Aircraft]:
        """
        Konvertiert einen OpenSky State Vector in ein Aircraft-Objekt.
        """
        try:
            if not state or len(state) < 17:
                self.error_count += 1
                return None
            
            # ICAO24 ist obligatorisch
            icao24 = state[0]
            if not icao24:
                self.error_count += 1
                return None
            
            aircraft = Aircraft(
                icao24=icao24,
                callsign=state[1].strip() if state[1] else None,
                origin_country=state[2] if state[2] else None,
                time_position=state[3] if state[3] else None,
                last_contact=state[4] if state[4] else None,
                longitude=state[5] if state[5] is not None else None,
                latitude=state[6] if state[6] is not None else None,
                baro_altitude=state[7] if state[7] is not None else None,
                on_ground=state[8] if state[8] is not None else None,
                velocity=state[9] if state[9] is not None else None,
                true_track=state[10] if state[10] is not None else None,
                vertical_rate=state[11] if state[11] is not None else None,
                sensors=state[12] if state[12] else None,
                geo_altitude=state[13] if state[13] is not None else None,
                squawk=state[14] if state[14] else None,
                spi=state[15] if state[15] is not None else None,
                position_source=state[16] if state[16] is not None else None
            )
            
            self.processed_count += 1
            return aircraft
            
        except Exception as e:
            print(f"Fehler beim Verarbeiten des State Vectors: {e}")
            self.error_count += 1
            return None
    
    def process_opensky_data(self, data: Dict[str, Any]) -> List[Aircraft]:
        """
        Verarbeitet komplette OpenSky API Antwort.
        """
        if not data or 'states' not in data:
            return []
        
        aircraft_list = []
        fetch_time = data.get('fetch_time')
        
        for state in data['states']:
            aircraft = self.parse_state_vector(state)
            if aircraft:
                aircraft.fetch_time = fetch_time
                aircraft_list.append(aircraft)
        
        return aircraft_list
    
    def filter_aircraft(self, aircraft_list: List[Aircraft], 
                       filters: Dict[str, Any] = None) -> List[Aircraft]:
        """
        Filtert Flugzeuge nach verschiedenen Kriterien.
        """
        if not filters:
            return aircraft_list
        
        filtered = aircraft_list
        
        if filters.get('only_airborne', False):
            filtered = [a for a in filtered if a.is_airborne()]
        
        if filters.get('only_with_position', False):
            filtered = [a for a in filtered if a.has_position()]
        
        if filters.get('country'):
            country = filters['country'].lower()
            filtered = [a for a in filtered if a.origin_country and 
                       country in a.origin_country.lower()]
        
        if filters.get('min_altitude') is not None:
            min_alt = filters['min_altitude']
            filtered = [a for a in filtered if a.baro_altitude and 
                       a.baro_altitude >= min_alt]
        
        if filters.get('max_altitude') is not None:
            max_alt = filters['max_altitude']
            filtered = [a for a in filtered if a.baro_altitude and 
                       a.baro_altitude <= max_alt]
        
        return filtered
    
    def get_statistics(self, aircraft_list: List[Aircraft]) -> Dict[str, Any]:
        """
        Berechnet Statistiken für eine Flugzeugliste. Returns:  Dictionary mit Statistiken
        """
        if not aircraft_list:
            return {
                'total_aircraft': 0,
                'airborne': 0,
                'on_ground': 0,
                'with_position': 0,
                'countries': [],
                'avg_altitude': None,
                'max_altitude': None,
                'min_altitude': None
            }
        
        airborne = [a for a in aircraft_list if a.is_airborne()]
        on_ground = [a for a in aircraft_list if not a.is_airborne()]
        with_position = [a for a in aircraft_list if a.has_position()]
        
        countries = list(set([a.origin_country for a in aircraft_list 
                            if a.origin_country]))
        
        altitudes = [a.baro_altitude for a in aircraft_list 
                    if a.baro_altitude is not None]
        
        return {
            'total_aircraft': len(aircraft_list),
            'airborne': len(airborne),
            'on_ground': len(on_ground),
            'with_position': len(with_position),
            'countries': sorted(countries),
            'country_count': len(countries),
            'avg_altitude': sum(altitudes) / len(altitudes) if altitudes else None,
            'max_altitude': max(altitudes) if altitudes else None,
            'min_altitude': min(altitudes) if altitudes else None,
            'processing_stats': {
                'processed_count': self.processed_count,
                'error_count': self.error_count
            }
        }
    
    def export_to_json(self, aircraft_list: List[Aircraft], 
                      filename: str = None) -> str:
        """
        Exportiert Flugzeugdaten zu JSON.
        """
        data = {
            'timestamp': datetime.now().isoformat(),
            'aircraft_count': len(aircraft_list),
            'aircraft': [aircraft.__dict__ for aircraft in aircraft_list]
        }
        
        json_string = json.dumps(data, indent=2, ensure_ascii=False)
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(json_string)
            print(f"Daten exportiert nach: {filename}")
        
        return json_string

def demo_data_processing():
    """Demonstriert die Datenverarbeitung mit echten OpenSky Daten."""
    # Import hier um zirkuläre Imports zu vermeiden
    from fetch_data import fetch_opensky_data
    
    print("=== DATENVERARBEITUNG DEMO ===")
    
    # 1. Daten von OpenSky API abrufen
    print("1. Abrufen der Live-Daten...")
    raw_data = fetch_opensky_data()
    
    if not raw_data:
        print("❌ Keine Daten erhalten!")
        return
    
    # 2. Daten verarbeiten
    print("2. Verarbeitung der Rohdaten...")
    processor = DataProcessor()
    aircraft_list = processor.process_opensky_data(raw_data)
    
    print(f"✓ {len(aircraft_list)} Flugzeuge verarbeitet")
    
    # 3. Statistiken anzeigen
    print("\n3. Statistiken:")
    stats = processor.get_statistics(aircraft_list)
    print(f"   Total: {stats['total_aircraft']}")
    print(f"   In der Luft: {stats['airborne']}")
    print(f"   Am Boden: {stats['on_ground']}")
    print(f"   Mit Position: {stats['with_position']}")
    print(f"   Länder: {stats['country_count']}")
    if stats['avg_altitude']:
        print(f"   Durchschnittshöhe: {stats['avg_altitude']:.0f}m")
    
    # 4. Filterbeispiele
    print("\n4. Filterbeispiele:")
    
    # Nur fliegende Flugzeuge mit Position
    airborne_with_pos = processor.filter_aircraft(aircraft_list, {
        'only_airborne': True,
        'only_with_position': True,
        'min_altitude': 1000  # Mindestens 1000m hoch
    })
    print(f"   Fliegende Flugzeuge >1000m: {len(airborne_with_pos)}")
    
    # Deutsche Flugzeuge
    german_aircraft = processor.filter_aircraft(aircraft_list, {
        'country': 'Germany'
    })
    print(f"   Deutsche Flugzeuge: {len(german_aircraft)}")
    
    # 5. Beispiel-Flugzeug im Detail
    if airborne_with_pos:
        print("\n5. Beispiel-Flugzeug:")
        example = airborne_with_pos[0]
        print(f"   ICAO24: {example.icao24}")
        print(f"   Callsign: {example.callsign or 'N/A'}")
        print(f"   Land: {example.origin_country or 'N/A'}")
        print(f"   Position: {example.latitude:.4f}, {example.longitude:.4f}")
        print(f"   Höhe: {example.baro_altitude:.0f}m ({example.get_altitude_feet():.0f}ft)")
        print(f"   Geschwindigkeit: {example.get_speed_kmh():.0f} km/h")
        print(f"   Kurs: {example.true_track:.0f}°")

if __name__ == "__main__":
    demo_data_processing()
