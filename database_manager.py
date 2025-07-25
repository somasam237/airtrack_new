"""
Database Manager fuer Airtrack PostgreSQL Integration
Verwaltet alle Database-Operationen mit psycopg2
"""

import psycopg2
import psycopg2.extras
from psycopg2.pool import SimpleConnectionPool
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

@dataclass
class DatabaseConfig:
    """Database-Konfiguration fuer PostgreSQL-Verbindung."""
    host: str = "localhost"
    port: int = 5432
    database: str = "airtrack_db"
    user: str = "postgres"
    password: str = "Samsam2002"
    min_connections: int = 1
    max_connections: int = 10

class AirtrackDatabase:
    """
    Hauptklasse fuer alle PostgreSQL-Operationen des Airtrack-Systems.
    """
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.connection_pool = None
        self.connected = False
        
        # Statistiken
        self.total_queries = 0
        self.total_errors = 0
        self.last_error = None
        
        print("🗄️ Airtrack Database Manager initialisiert")
        print(f"   Target: {self.config.host}:{self.config.port}/{self.config.database}")
    
    def connect(self) -> bool:
        """
        Stellt Verbindung zur PostgreSQL-Database her. Returns: True wenn erfolgreich, False bei Fehlern
        """
        try:
            print("🔌 Verbinde mit PostgreSQL...")
            
            # Connection Pool erstellen
            self.connection_pool = SimpleConnectionPool(
                self.config.min_connections,
                self.config.max_connections,
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password
            )
            
            # Test-Verbindung
            conn = self.get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                cursor.close()
                self.return_connection(conn)
                
                self.connected = True
                print(f"✅ PostgreSQL-Verbindung erfolgreich!")
                print(f"   Version: {version[:50]}...")
                return True
            
        except Exception as e:
            self.last_error = str(e)
            self.total_errors += 1
            print(f"❌ Database-Verbindung fehlgeschlagen: {e}")
            return False
        
        return False
    
    def get_connection(self):
        """Holt eine Verbindung aus dem Pool."""
        if not self.connection_pool:
            raise Exception("Database nicht verbunden! Rufe connect() auf.")
        return self.connection_pool.getconn()
    
    def return_connection(self, conn):
        """Gibt eine Verbindung an den Pool zurück."""
        if self.connection_pool and conn:
            self.connection_pool.putconn(conn)
    
    def close(self):
        """Schließt alle Database-Verbindungen."""
        if self.connection_pool:
            self.connection_pool.closeall()
            self.connected = False
            print("🔒 Database-Verbindungen geschlossen")
    
    def execute_query(self, query: str, params: tuple = None, fetch: str = None) -> Any:
        """
        Führt eine SQL-Query aus. Returns: Query-Ergebnis basierend auf fetch-Parameter
        """
        conn = None
        try:
            self.total_queries += 1
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cursor.execute(query, params)
            
            if fetch == 'one':
                result = cursor.fetchone()
            elif fetch == 'all':
                result = cursor.fetchall()
            elif fetch == 'many':
                result = cursor.fetchmany()
            else:
                result = None
            
            conn.commit()
            cursor.close()
            return result
            
        except Exception as e:
            self.total_errors += 1
            self.last_error = str(e)
            if conn:
                conn.rollback()
            print(f"❌ SQL-Fehler: {e}")
            print(f"   Query: {query[:100]}...")
            raise
        finally:
            if conn:
                self.return_connection(conn)
    
    # =====================================================
    # AIRCRAFT OPERATIONS
    # =====================================================
    
    def upsert_aircraft(self, aircraft_info: Dict[str, Any]) -> bool:
        """
        Fuegt Aircraft-Daten ein oder aktualisiert sie.
        """
        query = """
        INSERT INTO aircraft (
            icao24, registration, aircraft_type, manufacturer, model,
            airline, airline_iata, airline_icao, owner, operator,
            construction_number, first_flight, engines, seats, category,
            data_source, last_verified
        ) VALUES (
            %(icao24)s, %(registration)s, %(aircraft_type)s, %(manufacturer)s, %(model)s,
            %(airline)s, %(airline_iata)s, %(airline_icao)s, %(owner)s, %(operator)s,
            %(construction_number)s, %(first_flight)s, %(engines)s, %(seats)s, %(category)s,
            %(data_source)s, CURRENT_TIMESTAMP
        )
        ON CONFLICT (icao24) DO UPDATE SET
            registration = EXCLUDED.registration,
            aircraft_type = EXCLUDED.aircraft_type,
            manufacturer = EXCLUDED.manufacturer,
            model = EXCLUDED.model,
            airline = EXCLUDED.airline,
            airline_iata = EXCLUDED.airline_iata,
            airline_icao = EXCLUDED.airline_icao,
            owner = EXCLUDED.owner,
            operator = EXCLUDED.operator,
            construction_number = EXCLUDED.construction_number,
            first_flight = EXCLUDED.first_flight,
            engines = EXCLUDED.engines,
            seats = EXCLUDED.seats,
            category = EXCLUDED.category,
            data_source = EXCLUDED.data_source,
            updated_at = CURRENT_TIMESTAMP,
            last_verified = CURRENT_TIMESTAMP
        """
        
        # Standardwerte setzen
        aircraft_data = {
            'icao24': aircraft_info.get('icao24'),
            'registration': aircraft_info.get('registration'),
            'aircraft_type': aircraft_info.get('aircraft_type'),
            'manufacturer': aircraft_info.get('manufacturer'),
            'model': aircraft_info.get('model'),
            'airline': aircraft_info.get('airline'),
            'airline_iata': aircraft_info.get('airline_iata'),
            'airline_icao': aircraft_info.get('airline_icao'),
            'owner': aircraft_info.get('owner'),
            'operator': aircraft_info.get('operator'),
            'construction_number': aircraft_info.get('construction_number'),
            'first_flight': aircraft_info.get('first_flight'),
            'engines': aircraft_info.get('engines'),
            'seats': aircraft_info.get('seats'),
            'category': aircraft_info.get('category'),
            'data_source': aircraft_info.get('data_source', 'PYTHON')
        }
        
        try:
            self.execute_query(query, aircraft_data)
            return True
        except Exception as e:
            print(f"❌ Fehler beim Aircraft-Upsert für {aircraft_info.get('icao24')}: {e}")
            return False
    
    def get_aircraft(self, icao24: str) -> Optional[Dict]:
        """
        Ruft Aircraft-Informationen ab. Returns: Aircraft-Dictionary oder None
        """
        query = "SELECT * FROM aircraft WHERE icao24 = %s"
        result = self.execute_query(query, (icao24,), fetch='one')
        return dict(result) if result else None
    
    # =====================================================
    # FLIGHT OPERATIONS
    # =====================================================
    
    def create_or_get_flight(self, icao24: str, callsign: str = None, 
                           origin_country: str = None) -> int:
        """
        Erstellt einen neuen Flug oder gibt bestehende flight_id zurueck.
        """
        # Prüfe, ob bereits ein aktiver Flug existiert (letzte 4 Stunden)
        query_check = """
        SELECT flight_id FROM flights 
        WHERE icao24 = %s 
        AND last_seen > CURRENT_TIMESTAMP - INTERVAL '4 hours'
        ORDER BY last_seen DESC 
        LIMIT 1
        """
        
        existing_flight = self.execute_query(query_check, (icao24,), fetch='one')
        if existing_flight:
            return existing_flight['flight_id']
        
        # Aircraft muss existieren (Foreign Key Constraint)
        if not self.get_aircraft(icao24):
            # Erstelle minimalen Aircraft-Eintrag
            minimal_aircraft = {
                'icao24': icao24,
                'origin_country': origin_country,
                'data_source': 'AUTO_CREATED'
            }
            self.upsert_aircraft(minimal_aircraft)
        
        # Neuen Flug erstellen
        query_insert = """
        INSERT INTO flights (icao24, callsign, origin_country, first_seen, last_seen)
        VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        RETURNING flight_id
        """
        
        result = self.execute_query(
            query_insert, 
            (icao24, callsign, origin_country), 
            fetch='one'
        )
        
        flight_id = result['flight_id']
        print(f"🆕 Neuer Flug erstellt: flight_id={flight_id}, icao24={icao24}")
        return flight_id
    
    def add_flight_position(self, flight_id: int, position_data: Dict[str, Any]) -> bool:
        """
        Fuegt eine neue GPS-Position zu einem Flug hinzu. Returns: True wenn erfolgreich
        """
        query = """
        INSERT INTO flight_positions (
            flight_id, timestamp, latitude, longitude,
            altitude, geo_altitude, velocity, true_track, vertical_rate,
            on_ground, alert, spi
        ) VALUES (
            %(flight_id)s, %(timestamp)s, %(latitude)s, %(longitude)s,
            %(altitude)s, %(geo_altitude)s, %(velocity)s, %(true_track)s, %(vertical_rate)s,
            %(on_ground)s, %(alert)s, %(spi)s
        )
        """
        
        # Position-Daten vorbereiten
        pos_data = {
            'flight_id': flight_id,
            'timestamp': position_data.get('timestamp', datetime.now()),
            'latitude': position_data['latitude'],
            'longitude': position_data['longitude'],
            'altitude': position_data.get('altitude'),
            'geo_altitude': position_data.get('geo_altitude'),
            'velocity': position_data.get('velocity'),
            'true_track': position_data.get('true_track'),
            'vertical_rate': position_data.get('vertical_rate'),
            'on_ground': position_data.get('on_ground'),
            'alert': position_data.get('alert', False),
            'spi': position_data.get('spi', False)
        }
        
        try:
            self.execute_query(query, pos_data)
            
            # Update flight last_seen
            self.execute_query(
                "UPDATE flights SET last_seen = CURRENT_TIMESTAMP WHERE flight_id = %s",
                (flight_id,)
            )
            
            return True
        except Exception as e:
            print(f"❌ Fehler beim Hinzufügen der Position für flight_id {flight_id}: {e}")
            return False
    
    def calculate_flight_statistics(self, flight_id: int) -> bool:
        """
        Berechnet Statistiken für einen Flug (nutzt die SQL-Funktion).
        """
        try:
            self.execute_query("SELECT calculate_flight_statistics(%s)", (flight_id,))
            return True
        except Exception as e:
            print(f"❌ Fehler bei Statistik-Berechnung für flight_id {flight_id}: {e}")
            return False
    
    # =====================================================
    # BATCH OPERATIONS
    # =====================================================
    
    def process_aircraft_batch(self, aircraft_list: List[Any]) -> Dict[str, int]:
        """
        Verarbeitet eine komplette Batch von Aircraft-Objekten.
        """
        print(f"🚀 Verarbeite Batch von {len(aircraft_list)} Aircraft...")
        
        stats = {
            'total_aircraft': len(aircraft_list),
            'new_flights': 0,
            'positions_added': 0,
            'aircraft_updated': 0,
            'errors': 0
        }
        
        start_time = datetime.now()
        
        for aircraft in aircraft_list:
            try:
                # 1. Aircraft-Info aktualisieren (falls verfügbar)
                if hasattr(aircraft, 'aircraft_info') and aircraft.aircraft_info:
                    if self.upsert_aircraft(aircraft.aircraft_info):
                        stats['aircraft_updated'] += 1
                
                # 2. Flug erstellen oder finden
                flight_id = self.create_or_get_flight(
                    aircraft.icao24,
                    aircraft.callsign,
                    aircraft.origin_country
                )
                
                if not hasattr(aircraft, '_db_flight_id'):
                    stats['new_flights'] += 1
                    aircraft._db_flight_id = flight_id
                
                # 3. Position hinzufügen (falls verfügbar)
                if aircraft.has_position():
                    position_data = {
                        'timestamp': aircraft.fetch_time or datetime.now(),
                        'latitude': aircraft.latitude,
                        'longitude': aircraft.longitude,
                        'altitude': aircraft.baro_altitude,
                        'geo_altitude': aircraft.geo_altitude,
                        'velocity': aircraft.velocity,
                        'true_track': aircraft.true_track,
                        'vertical_rate': aircraft.vertical_rate,
                        'on_ground': aircraft.on_ground
                    }
                    
                    if self.add_flight_position(flight_id, position_data):
                        stats['positions_added'] += 1
                
                # 4. Statistiken berechnen (alle 10 Positionen)
                if stats['positions_added'] % 10 == 0:
                    self.calculate_flight_statistics(flight_id)
                
            except Exception as e:
                stats['errors'] += 1
                print(f"❌ Fehler bei Aircraft {aircraft.icao24}: {e}")
        
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"✅ Batch-Verarbeitung abgeschlossen in {duration:.1f}s:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        return stats
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """
        Gibt umfassende Database-Statistiken zurück.
        
        Returns:
            Dictionary mit allen wichtigen Metriken
        """
        stats = {}
        
        try:
            # Datensatz-Zählung
            counts_query = """
            SELECT 
                (SELECT COUNT(*) FROM aircraft) as aircraft_count,
                (SELECT COUNT(*) FROM flights) as flights_count,
                (SELECT COUNT(*) FROM flight_positions) as positions_count
            """
            counts = self.execute_query(counts_query, fetch='one')
            stats['record_counts'] = dict(counts) if counts else {}
            
            # Performance-Statistiken
            stats['performance'] = {
                'total_queries': self.total_queries,
                'total_errors': self.total_errors,
                'last_error': self.last_error
            }
            
        except Exception as e:
            print(f"❌ Fehler beim Abrufen der Database-Statistiken: {e}")
            stats['error'] = str(e)
        
        return stats

def create_database_config_from_env() -> DatabaseConfig:
    """
    Erstellt Database-Config aus Environment-Variablen 
    """
    # Versuche .env-Datei zu laden
    env_file = Path('.env')
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
    
    return DatabaseConfig(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '5432')),
        database=os.getenv('DB_NAME', 'airtrack_db'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'Samsam2002'),
        min_connections=int(os.getenv('DB_MIN_CONN', '1')),
        max_connections=int(os.getenv('DB_MAX_CONN', '10'))
    )

def demo_database_operations():
    """Demonstriert die Database-Operationen."""
    print("=== AIRTRACK DATABASE OPERATIONS DEMO ===")
    
    # Config aus .env laden
    config = create_database_config_from_env()
    print(f"📋 Database Config: {config.user}@{config.host}:{config.port}/{config.database}")
    
    # Database Manager initialisieren
    db = AirtrackDatabase(config)
    
    try:
        # Verbindung herstellen
        if not db.connect():
            print("❌ Kann nicht zur Database verbinden!")
            return
        
        # Test-Aircraft hinzufügen
        print("\n--- TEST: Aircraft hinzufügen ---")
        test_aircraft = {
            'icao24': 'test123',
            'registration': 'D-TEST',
            'aircraft_type': 'Test Aircraft',
            'manufacturer': 'Test Manufacturer',
            'airline': 'Test Airlines',
            'category': 'Commercial',
            'data_source': 'DEMO'
        }
        
        if db.upsert_aircraft(test_aircraft):
            print("✅ Test-Aircraft hinzugefügt")
        
        # Test-Flug erstellen
        print("\n--- TEST: Flug erstellen ---")
        flight_id = db.create_or_get_flight('test123', 'TST123', 'Germany')
        print(f"✅ Flight ID: {flight_id}")
        
        # Test-Position hinzufügen
        print("\n--- TEST: Position hinzufügen ---")
        test_position = {
            'latitude': 52.5200,  # Berlin
            'longitude': 13.4050,
            'altitude': 10000,
            'velocity': 250,
            'on_ground': False
        }
        
        if db.add_flight_position(flight_id, test_position):
            print("✅ Test-Position hinzugefügt")
        
        # Statistiken berechnen
        print("\n--- TEST: Statistiken berechnen ---")
        if db.calculate_flight_statistics(flight_id):
            print("✅ Statistiken berechnet")
        
        # Database-Statistiken abrufen
        print("\n--- DATABASE STATISTIKEN ---")
        stats = db.get_database_statistics()
        
        if 'record_counts' in stats:
            counts = stats['record_counts']
            print(f"📊 Aircraft: {counts.get('aircraft_count', 0)}")
            print(f"📊 Flights: {counts.get('flights_count', 0)}")
            print(f"📊 Positions: {counts.get('positions_count', 0)}")
        
        if 'performance' in stats:
            perf = stats['performance']
            print(f"🔧 Queries: {perf.get('total_queries', 0)}")
            print(f"🔧 Errors: {perf.get('total_errors', 0)}")
        
    except Exception as e:
        print(f"❌ Demo-Fehler: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    demo_database_operations()
