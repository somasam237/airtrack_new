"""
Database-integrierter Flight Tracker
Erweitert den bestehenden FlightTracker um PostgreSQL-Persistierung
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

# Imports aus bestehendem System
from data_processor import Aircraft
from flight_tracker import Flight, FlightTracker
from aircraft_database import AircraftDatabase
from database_manager import AirtrackDatabase, DatabaseConfig

class DatabaseFlightTracker(FlightTracker):
    """
    Erweiterte Version des FlightTrackers mit PostgreSQL-Integration.
    """
    
    def __init__(self, max_flight_age_hours: int = 24, aircraft_db: AircraftDatabase = None,
                 db_config: DatabaseConfig = None, enable_database: bool = True):
        """
        Initialisiert Database-integrierten FlightTracker.
        """
        # Basis FlightTracker initialisieren (nur max_flight_age_hours)
        super().__init__(max_flight_age_hours)
        
        # Aircraft Database separat setzen
        self.aircraft_db = aircraft_db
        self.enrichment_enabled = aircraft_db is not None
        self.enriched_flights_count = 0
        
        # Database-Integration
        self.database_enabled = enable_database
        self.airtrack_db = None
        self.db_connected = False
        
        # Statistiken
        self.total_database_writes = 0
        self.database_errors = 0
        self.last_database_sync = None
        
        if self.database_enabled:
            self._initialize_database(db_config)
        else:
            print("⚠️ Database-Integration deaktiviert (Memory-only Mode)")
    
    def _initialize_database(self, db_config: DatabaseConfig = None):
        """Initialisiert die Database-Verbindung."""
        try:
            print("🗄️ Initialisiere PostgreSQL-Integration...")
            
            # Default-Config falls nicht angegeben
            if not db_config:
                from database_manager import create_database_config_from_env
                db_config = create_database_config_from_env()
            
            # Database Manager erstellen
            self.airtrack_db = AirtrackDatabase(db_config)
            
            # Verbindung herstellen
            if self.airtrack_db.connect():
                self.db_connected = True
                print("✅ PostgreSQL erfolgreich verbunden!")
                print("🔄 Flight Tracker mit Database-Persistierung aktiv")
            else:
                print("❌ PostgreSQL-Verbindung fehlgeschlagen - Fallback zu Memory-only")
                self.database_enabled = False
                
        except Exception as e:
            print(f"❌ Database-Initialisierung fehlgeschlagen: {e}")
            print("🔄 Fallback zu Memory-only Mode")
            self.database_enabled = False
    
    def update_flights(self, aircraft_list: List[Aircraft]):
        """
        Erweiterte update_flights Methode mit Database-Integration.
        """
        # 1. Standard Memory-Update
        super().update_flights(aircraft_list)
        
        # 2. Database-Persistierung (falls aktiviert)
        if self.database_enabled and self.db_connected:
            try:
                stats = self.airtrack_db.process_aircraft_batch(aircraft_list)
                self.total_database_writes += stats.get('positions_added', 0)
                self.last_database_sync = datetime.now()
                
                print(f"💾 Database-Sync: {stats.get('positions_added', 0)} Positionen, "
                      f"{stats.get('new_flights', 0)} neue Flüge")
                
            except Exception as e:
                self.database_errors += 1
                print(f"❌ Database-Sync Fehler: {e}")
    
    def get_flight_statistics(self) -> Dict:
        """
        Erweiterte Statistiken mit Database-Daten.
        """
        # Standard Memory-Statistiken
        memory_stats = super().get_flight_statistics()
        
        # Database-Statistiken hinzufügen
        if self.database_enabled and self.db_connected:
            try:
                db_stats = self.airtrack_db.get_database_statistics()
                
                # Kombinierte Statistiken
                combined_stats = memory_stats.copy()
                combined_stats.update({
                    'database_enabled': True,
                    'database_connected': self.db_connected,
                    'total_database_writes': self.total_database_writes,
                    'database_errors': self.database_errors,
                    'last_database_sync': self.last_database_sync.isoformat() if self.last_database_sync else None,
                    'database_record_counts': db_stats.get('record_counts', {}),
                    'database_performance': db_stats.get('performance', {})
                })
                
                return combined_stats
                
            except Exception as e:
                print(f"❌ Fehler beim Abrufen der Database-Statistiken: {e}")
                memory_stats['database_error'] = str(e)
        
        else:
            memory_stats.update({
                'database_enabled': False,
                'database_connected': False
            })
        
        return memory_stats
    
    def get_database_dashboard(self) -> Dict[str, Any]:
        """
        Ruft Dashboard-Daten aus der Database ab.
        """
        if not (self.database_enabled and self.db_connected):
            return {'error': 'Database nicht verfügbar'}
        
        try:
            # Einfache Dashboard-Metriken
            stats = self.airtrack_db.get_database_statistics()
            
            # Simuliere Summary-Metriken (da Views möglicherweise noch nicht funktionieren)
            summary_metrics = []
            if 'record_counts' in stats:
                counts = stats['record_counts']
                summary_metrics = [
                    {'metric': 'Active Flights', 'value': counts.get('flights_count', 0), 'timeframe': 'Current'},
                    {'metric': 'Total Aircraft', 'value': counts.get('aircraft_count', 0), 'timeframe': 'All time'},
                    {'metric': 'Total Positions', 'value': counts.get('positions_count', 0), 'timeframe': 'All time'}
                ]
            
            dashboard_data = {
                'summary_metrics': summary_metrics,
                'database_stats': stats
            }
            return dashboard_data
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_historical_flights(self, hours: int = 24) -> List[Dict]:
        """
        Ruft historische Flüge aus der Database ab.
        """
        if not (self.database_enabled and self.db_connected):
            print("⚠️ Database nicht verfügbar für historische Daten")
            return []
        
        try:
            # Einfache Abfrage für historische Flüge
            query = """
            SELECT flight_id, icao24, callsign, origin_country, flight_status, 
                   first_seen, last_seen, position_count
            FROM flights 
            WHERE last_seen > CURRENT_TIMESTAMP - INTERVAL '%s hours'
            ORDER BY last_seen DESC
            LIMIT 100
            """
            
            result = self.airtrack_db.execute_query(query % hours, fetch='all')
            return [dict(row) for row in result] if result else []
            
        except Exception as e:
            print(f"❌ Fehler beim Abrufen historischer Flüge: {e}")
            return []
    
    def get_all_stored_flights(self, limit: int = 5000) -> List[Dict]:
        """
        Ruft ALLE gespeicherten Flüge aus der Database ab.
        
        Args:
            limit: Maximale Anzahl zurückzugebender Flüge
            
        Returns:
            Liste aller Flight-Dictionaries aus der Database
        """
        if not (self.database_enabled and self.db_connected):
            print("⚠️ Database nicht verfügbar für alle Flüge")
            return []
        
        try:
            # Erweiterte Abfrage für alle Flüge mit aktuellster Position
            query = """
            SELECT DISTINCT ON (f.icao24) 
                   f.flight_id, f.icao24, f.callsign, f.origin_country, 
                   f.flight_status, f.first_seen, f.last_seen, f.position_count,
                   p.latitude, p.longitude, p.altitude, p.velocity, 
                   p.true_track, p.on_ground, p.timestamp as fetch_time
            FROM flights f
            LEFT JOIN positions p ON f.flight_id = p.flight_id
            WHERE p.timestamp = (
                SELECT MAX(timestamp) 
                FROM positions p2 
                WHERE p2.flight_id = f.flight_id
            )
            ORDER BY f.icao24, f.last_seen DESC
            LIMIT %s
            """
            
            result = self.airtrack_db.execute_query(query, (limit,), fetch='all')
            
            flights = []
            for row in result:
                flight_data = {
                    'flight_id': row[0],
                    'icao24': row[1], 
                    'callsign': row[2],
                    'origin_country': row[3],
                    'flight_status': row[4],
                    'first_seen': row[5].isoformat() if row[5] else None,
                    'last_seen': row[6].isoformat() if row[6] else None,
                    'position_count': row[7],
                    'latitude': float(row[8]) if row[8] else None,
                    'longitude': float(row[9]) if row[9] else None,
                    'altitude': float(row[10]) if row[10] else None,
                    'velocity': float(row[11]) if row[11] else None,
                    'true_track': float(row[12]) if row[12] else None,
                    'on_ground': bool(row[13]) if row[13] is not None else None,
                    'fetch_time': row[14].isoformat() if row[14] else None
                }
                flights.append(flight_data)
            
            print(f"📊 Alle gespeicherten Flüge abgerufen: {len(flights)} Flüge")
            return flights
            
        except Exception as e:
            print(f"❌ Fehler beim Abrufen aller Flüge: {e}")
            return []
    
    def close(self):
        """Schließt alle Verbindungen sauber."""
        if self.airtrack_db:
            self.airtrack_db.close()
        print("🔒 Database Flight Tracker geschlossen")

def demo_database_flight_tracking():
    """
    Demonstriert das Database-integrierte Flight Tracking.
    """
    print("=== DATABASE FLIGHT TRACKING DEMO ===")
    print("Live Flight Tracking mit PostgreSQL-Persistierung")
    
    # Database-Config aus .env
    from database_manager import create_database_config_from_env
    db_config = create_database_config_from_env()
    
    # Aircraft Database für Anreicherung
    aircraft_db = AircraftDatabase()
    
    # Sample-Database laden
    try:
        from aircraft_database import create_sample_aircraft_database
        sample_file = create_sample_aircraft_database()
        aircraft_db.load_csv_database(sample_file)
    except:
        print("⚠️ Konnte Sample Aircraft Database nicht laden")
    
    # Database Flight Tracker initialisieren
    tracker = DatabaseFlightTracker(
        aircraft_db=aircraft_db,
        db_config=db_config,
        enable_database=True
    )
    
    if not tracker.db_connected:
        print("❌ Demo kann nicht fortgesetzt werden - Database-Verbindung fehlgeschlagen")
        print("💡 Prüfe deine PostgreSQL-Verbindungseinstellungen!")
        return
    
    try:
        # Teste mit echten Daten (falls verfügbar)
        print("\n--- TESTE MIT LIVE-DATEN ---")
        
        from airtrack_main import fetch_opensky_data
        from data_processor import DataProcessor
        
        processor = DataProcessor()
        
        # Ein Zyklus Live-Daten
        print("🌐 Rufe Live-Daten von OpenSky ab...")
        raw_data = fetch_opensky_data()
        
        if raw_data:
            aircraft_list = processor.process_opensky_data(raw_data)
            
            # Filter für Demo (nur 10 Flugzeuge mit Position)
            filtered_aircraft = processor.filter_aircraft(aircraft_list, {
                'only_with_position': True
            })[:10]
            
            print(f"🔍 Verarbeite {len(filtered_aircraft)} Flugzeuge...")
            
            # Tracking mit Database-Persistierung
            tracker.update_flights(filtered_aircraft)
            
            # Statistiken anzeigen
            print("\n📊 KOMBINIERTE STATISTIKEN:")
            stats = tracker.get_flight_statistics()
            
            print(f"   Memory Flüge: {stats.get('active_flights', 0)}")
            print(f"   Database Writes: {stats.get('total_database_writes', 0)}")
            print(f"   Database Errors: {stats.get('database_errors', 0)}")
            
            if 'database_record_counts' in stats:
                db_counts = stats['database_record_counts']
                print(f"   DB Aircraft: {db_counts.get('aircraft_count', 0)}")
                print(f"   DB Flights: {db_counts.get('flights_count', 0)}")
                print(f"   DB Positions: {db_counts.get('positions_count', 0)}")
            
        else:
            print("⚠️ Keine Live-Daten verfügbar - Demo mit Testdaten")
            
            # Testdaten erstellen
            test_aircraft = Aircraft(
                icao24='test789',
                callsign='TEST789',
                origin_country='Germany',
                latitude=52.5200,
                longitude=13.4050,
                baro_altitude=10000,
                velocity=250,
                on_ground=False
            )
            
            tracker.update_flights([test_aircraft])
            print("✅ Testdaten verarbeitet")
    
    except KeyboardInterrupt:
        print("\n🛑 Demo gestoppt")
    except Exception as e:
        print(f"❌ Demo-Fehler: {e}")
    finally:
        tracker.close()

if __name__ == "__main__":
    demo_database_flight_tracking()
