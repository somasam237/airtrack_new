import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from data_processor import Aircraft

@dataclass
class FlightPosition:
    """Einzelne Position eines Flugzeugs zu einem bestimmten Zeitpunkt."""
    timestamp: str
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    velocity: Optional[float] = None
    true_track: Optional[float] = None
    vertical_rate: Optional[float] = None
    on_ground: Optional[bool] = None

@dataclass
class Flight:
    """
    Repraesentiert einen kompletten Flug mit allen gesammelten Positionen.
    """
    icao24: str
    callsign: Optional[str] = None
    origin_country: Optional[str] = None
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    positions: List[FlightPosition] = field(default_factory=list)
    flight_status: str = "unknown"  # unknown, ground, takeoff, airborne, landing, landed
    
    # Berechnete Eigenschaften
    max_altitude: Optional[float] = None
    min_altitude: Optional[float] = None
    max_speed: Optional[float] = None
    total_distance: Optional[float] = None
    
    def add_position(self, aircraft: Aircraft):
        """Fuegt eine neue Position zum Flug hinzu."""
        if not aircraft.has_position():
            return
        
        position = FlightPosition(
            timestamp=aircraft.fetch_time or datetime.now().isoformat(),
            latitude=aircraft.latitude,
            longitude=aircraft.longitude,
            altitude=aircraft.baro_altitude,
            velocity=aircraft.velocity,
            true_track=aircraft.true_track,
            vertical_rate=aircraft.vertical_rate,
            on_ground=aircraft.on_ground
        )
        
        self.positions.append(position)
        
        # Zeitstempel aktualisieren
        if not self.first_seen:
            self.first_seen = position.timestamp
        self.last_seen = position.timestamp
        
        # Callsign und Land aktualisieren (falls verfügbar)
        if aircraft.callsign and not self.callsign:
            self.callsign = aircraft.callsign
        if aircraft.origin_country and not self.origin_country:
            self.origin_country = aircraft.origin_country
        
        # Flugstatus aktualisieren
        self._update_flight_status()
        
        # Statistiken neu berechnen
        self._calculate_statistics()
    
    def _update_flight_status(self):
        """Aktualisiert den Flugstatus basierend auf den letzten Positionen."""
        if not self.positions:
            return
        
        recent_positions = self.positions[-5:]  # Letzte 5 Positionen
        
        # Prüfe, ob am Boden
        ground_count = sum(1 for pos in recent_positions if pos.on_ground)
        if ground_count >= len(recent_positions) // 2:
            self.flight_status = "ground"
            return
        
        # Prüfe Höhenänderungen für Start/Landung
        if len(self.positions) >= 3:
            altitudes = [pos.altitude for pos in recent_positions if pos.altitude is not None]
            if len(altitudes) >= 2:
                altitude_trend = altitudes[-1] - altitudes[0] if len(altitudes) > 1 else 0
                current_altitude = altitudes[-1]
                
                if current_altitude < 1000 and altitude_trend > 50:  # Steigend, niedrig
                    self.flight_status = "takeoff"
                elif current_altitude < 1000 and altitude_trend < -50:  # Sinkend, niedrig
                    self.flight_status = "landing"
                elif current_altitude > 1000:
                    self.flight_status = "airborne"
    
    def _calculate_statistics(self):
        """Berechnet Flugstatistiken."""
        if not self.positions:
            return
        
        # Höhenstatistiken
        altitudes = [pos.altitude for pos in self.positions if pos.altitude is not None]
        if altitudes:
            self.max_altitude = max(altitudes)
            self.min_altitude = min(altitudes)
        
        # Geschwindigkeitsstatistik
        velocities = [pos.velocity for pos in self.positions if pos.velocity is not None]
        if velocities:
            self.max_speed = max(velocities)
        
        # Gesamtdistanz berechnen
        self.total_distance = self._calculate_total_distance()
    
    def _calculate_total_distance(self) -> float:
        """Berechnet die Gesamtflugdistanz in Kilometern."""
        if len(self.positions) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(1, len(self.positions)):
            pos1 = self.positions[i-1]
            pos2 = self.positions[i]
            distance = self._haversine_distance(
                pos1.latitude, pos1.longitude,
                pos2.latitude, pos2.longitude
            )
            total_distance += distance
        
        return total_distance
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Berechnet die Entfernung zwischen zwei GPS-Punkten in Kilometern."""
        R = 6371  # Erdradius in km
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def get_duration_minutes(self) -> Optional[float]:
        """Berechnet die Flugdauer in Minuten."""
        if not self.first_seen or not self.last_seen:
            return None
        
        try:
            start = datetime.fromisoformat(self.first_seen.replace('Z', '+00:00'))
            end = datetime.fromisoformat(self.last_seen.replace('Z', '+00:00'))
            duration = end - start
            return duration.total_seconds() / 60
        except:
            return None
    
    def get_flight_path(self) -> List[Tuple[float, float]]:
        """Gibt die Flugbahn als Liste von (lat, lon) Tupeln zurueck."""
        return [(pos.latitude, pos.longitude) for pos in self.positions]
    
    def is_active(self, max_age_minutes: int = 30) -> bool:
        """Prueft, ob der Flug noch aktiv ist (letzte Position nicht aelter als X Minuten)."""
        if not self.last_seen:
            return False
        
        try:
            last_update = datetime.fromisoformat(self.last_seen.replace('Z', '+00:00'))
            now = datetime.now()
            age = now - last_update
            return age.total_seconds() / 60 <= max_age_minutes
        except:
            return False

class FlightTracker:
    """
    Verwaltet alle aktiven Fluege und führt Einzelpositionen zu Flugbahnen zusammen.
    """
    
    def __init__(self, max_flight_age_hours: int = 24):
        self.flights: Dict[str, Flight] = {}  # icao24 -> Flight
        self.max_flight_age_hours = max_flight_age_hours
        self.total_updates = 0
        self.total_flights_tracked = 0
    
    def update_flights(self, aircraft_list: List[Aircraft]):
       
        self.total_updates += 1
        new_flights = 0
        
        for aircraft in aircraft_list:
            if not aircraft.has_position():
                continue
            
            icao24 = aircraft.icao24
            
            # Neuen Flug erstellen oder existierenden aktualisieren
            if icao24 not in self.flights:
                flight = Flight(icao24=icao24)
                self.flights[icao24] = flight
                self.total_flights_tracked += 1
                new_flights += 1
            
            
            self.flights[icao24].add_position(aircraft)
        
        # Alte Fluege aufräumen
        self._cleanup_old_flights()
        
        print(f"✓ {len(aircraft_list)} Aircraft verarbeitet | "
              f"{new_flights} neue Flüge | "
              f"{len(self.flights)} aktive Flüge")
    
    def _cleanup_old_flights(self):
        """Entfernt alte, inaktive Fluege."""
        cutoff_time = datetime.now() - timedelta(hours=self.max_flight_age_hours)
        
        old_flights = []
        for icao24, flight in self.flights.items():
            if not flight.is_active(max_age_minutes=60):  # 1 Stunde inaktiv
                try:
                    last_update = datetime.fromisoformat(flight.last_seen.replace('Z', '+00:00'))
                    if last_update < cutoff_time:
                        old_flights.append(icao24)
                except:
                    old_flights.append(icao24)
        
        for icao24 in old_flights:
            del self.flights[icao24]
        
        if old_flights:
            print(f"🗑 {len(old_flights)} alte Fluege entfernt")
    
    def get_active_flights(self) -> List[Flight]:
        """Gibt alle aktiven Fluege zurueck."""
        return [flight for flight in self.flights.values() if flight.is_active()]
    
    def get_flights_by_status(self, status: str) -> List[Flight]:
        """Gibt Fluege mit einem bestimmten Status zurueck."""
        return [flight for flight in self.flights.values() 
                if flight.flight_status == status and flight.is_active()]
    
    def get_flight_statistics(self) -> Dict:
        """Berechnet Statistiken über alle verfolgten Flüge."""
        active_flights = self.get_active_flights()
        
        if not active_flights:
            return {
                'total_tracked_flights': self.total_flights_tracked,
                'active_flights': 0,
                'updates_processed': self.total_updates
            }
        
        # Status-Verteilung
        status_counts = {}
        for flight in active_flights:
            status = flight.flight_status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Durchschnittswerte
        durations = [flight.get_duration_minutes() for flight in active_flights 
                    if flight.get_duration_minutes() is not None]
        distances = [flight.total_distance for flight in active_flights 
                    if flight.total_distance is not None]
        
        return {
            'total_tracked_flights': self.total_flights_tracked,
            'active_flights': len(active_flights),
            'updates_processed': self.total_updates,
            'status_distribution': status_counts,
            'avg_duration_minutes': sum(durations) / len(durations) if durations else 0,
            'avg_distance_km': sum(distances) / len(distances) if distances else 0,
            'longest_flight_minutes': max(durations) if durations else 0,
            'longest_distance_km': max(distances) if distances else 0
        }
    
    def export_flights_to_json(self, filename: str = None, 
                              only_active: bool = True) -> str:
        """
        Exportiert Flugdaten zu JSON.
        """
        flights_to_export = self.get_active_flights() if only_active else list(self.flights.values())
        
        # Konvertiere zu Dictionary für JSON-Serialisierung
        flights_data = []
        for flight in flights_to_export:
            flight_dict = {
                'icao24': flight.icao24,
                'callsign': flight.callsign,
                'origin_country': flight.origin_country,
                'first_seen': flight.first_seen,
                'last_seen': flight.last_seen,
                'flight_status': flight.flight_status,
                'max_altitude': flight.max_altitude,
                'min_altitude': flight.min_altitude,
                'max_speed': flight.max_speed,
                'total_distance': flight.total_distance,
                'duration_minutes': flight.get_duration_minutes(),
                'positions': [
                    {
                        'timestamp': pos.timestamp,
                        'latitude': pos.latitude,
                        'longitude': pos.longitude,
                        'altitude': pos.altitude,
                        'velocity': pos.velocity,
                        'true_track': pos.true_track,
                        'on_ground': pos.on_ground
                    }
                    for pos in flight.positions
                ]
            }
            flights_data.append(flight_dict)
        
        data = {
            'export_timestamp': datetime.now().isoformat(),
            'flight_count': len(flights_data),
            'statistics': self.get_flight_statistics(),
            'flights': flights_data
        }
        
        json_string = json.dumps(data, indent=2, ensure_ascii=False)
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(json_string)
            print(f"Flugdaten exportiert nach: {filename}")
        
        return json_string

def demo_flight_tracking():
    """Demonstriert das Flight Tracking mit echten Daten."""
    from airtrack_main import fetch_opensky_data
    from data_processor import DataProcessor
    
    print("=== FLIGHT TRACKING DEMO ===")
    print("Sammelt mehrere Datenzyklen und verfolgt Flugbahnen...")
    
    tracker = FlightTracker()
    processor = DataProcessor()
    
    cycles = 3  # Anzahl der Datenzyklen
    interval = 30  # Sekunden zwischen den Zyklen
    
    try:
        for cycle in range(1, cycles + 1):
            print(f"\n--- Zyklus {cycle}/{cycles} ---")
            
            # Daten abrufen und verarbeiten
            raw_data = fetch_opensky_data()
            if raw_data:
                aircraft_list = processor.process_opensky_data(raw_data)
                
                # Filter für bessere Demo (nur fliegende Flugzeuge mit Position)
                filtered_aircraft = processor.filter_aircraft(aircraft_list, {
                    'only_airborne': True,
                    'only_with_position': True
                })
                
                # Flüge aktualisieren
                tracker.update_flights(filtered_aircraft)
                
                # Statistiken anzeigen
                stats = tracker.get_flight_statistics()
                print(f"📊 Aktive Fluege: {stats['active_flights']}")
                print(f"📊 Status-Verteilung: {stats['status_distribution']}")
                
                # Zeige Beispiel-Flüge
                active_flights = tracker.get_active_flights()
                if active_flights:
                    print("\n🛩 Beispiel-Fluege:")
                    for flight in active_flights[:3]:
                        duration = flight.get_duration_minutes()
                        distance = flight.total_distance or 0
                        print(f"   {flight.icao24} ({flight.callsign or 'N/A'}): "
                              f"{len(flight.positions)} Positionen, "
                              f"{duration:.1f}min, "
                              f"{distance:.1f}km, "
                              f"Status: {flight.flight_status}")
            
            if cycle < cycles:
                print(f"⏱ Warte {interval} Sekunden bis zum naechsten Zyklus...")
                time.sleep(interval)
        
        # Final Export
        print(f"\n=== FINAL EXPORT ===")
        filename = f"flight_tracks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        tracker.export_flights_to_json(filename)
        
        # Finale Statistiken
        final_stats = tracker.get_flight_statistics()
        print(f"\n📈 FINALE STATISTIKEN:")
        for key, value in final_stats.items():
            print(f"   {key}: {value}")
            
    except KeyboardInterrupt:
        print("\n🛑 Flight Tracking gestoppt")
        
        # Export auch bei Abbruch
        filename = f"flight_tracks_partial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        tracker.export_flights_to_json(filename)

if __name__ == "__main__":
    import time
    demo_flight_tracking()
