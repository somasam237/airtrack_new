"""
Airtrack Web Server
Flask-basierte Web-Anwendung für interaktive Flight Map Visualization
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import threading
import time

# Airtrack Imports
from database_flight_tracker import DatabaseFlightTracker
from database_manager import create_database_config_from_env
from aircraft_database import AircraftDatabase
from airtrack_main import fetch_opensky_data
from data_processor import DataProcessor
from flight_routes_service import flight_routes_service

class AirtrackWebServer:
    """
    Web Server für Airtrack Flight Visualization
    
    Features:
    Interaktive Leaflet-Karte
    Real-time Flight Updates via WebSocket
    Live Dashboard mit Statistiken
    Aircraft Info Popups
     Historical Data Visualization
    """
    
    def __init__(self, host='127.0.0.1', port=5000, debug=False):
        # Flask app mit templates/static als static folder
        self.app = Flask(__name__, 
                        static_folder='templates/static',
                        template_folder='templates')
        self.app.config['SECRET_KEY'] = 'airtrack_secret_key_2025'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self.host = host
        self.port = port
        self.debug = debug
        
        # Airtrack Components
        self.flight_tracker = None
        self.aircraft_db = None
        self.data_processor = DataProcessor()
        
        # Live Update Control
        self.live_updates_enabled = False
        self.update_thread = None
        self.update_interval = 30  # Sekunden
        
        # Setup routes and WebSocket handlers
        self._setup_routes()
        self._setup_websocket_handlers()
        
        print(" Airtrack Web Server initialisiert")
        print(f"   Host: {self.host}:{self.port}")
    
    def initialize_airtrack(self):
        """Initialisiert die Airtrack-Komponenten."""
        try:
            print(" Initialisiere Airtrack-Komponenten...")
            
            # Database Config
            db_config = create_database_config_from_env()
            
            # Aircraft Database
            self.aircraft_db = AircraftDatabase()
            try:
                from aircraft_database import create_sample_aircraft_database
                sample_file = create_sample_aircraft_database()
                self.aircraft_db.load_csv_database(sample_file)
                print(" Aircraft Database geladen")
            except Exception as e:
                print(f" Aircraft Database Fehler: {e}")
            
            # Flight Tracker mit Database
            self.flight_tracker = DatabaseFlightTracker(
                aircraft_db=self.aircraft_db,
                db_config=db_config,
                enable_database=True
            )
            
            if self.flight_tracker.db_connected:
                print(" Airtrack-Komponenten erfolgreich initialisiert")
                return True
            else:
                print(" Database-Verbindung fehlgeschlagen")
                return False
                
        except Exception as e:
            print(f"❌ Airtrack-Initialisierung fehlgeschlagen: {e}")
            return False
    
    def _setup_routes(self):
        """Setup Flask-Routen."""
        
        @self.app.route('/')
        def index():
            """Hauptseite mit interaktiver Karte."""
            return render_template('index.html')
        
        @self.app.route('/api/flights/current')
        def get_current_flights():
            """API: Aktuelle Flüge für die Karte."""
            if not self.flight_tracker:
                return jsonify({'error': 'Flight Tracker nicht initialisiert'})
            
            try:
                # Memory-Flüge holen
                active_flights = self.flight_tracker.get_active_flights()
                
                # Format für Karte
                flight_data = []
                for flight in active_flights:
                    if flight.positions:
                        latest_pos = flight.positions[-1]
                        
                        # Route-Informationen holen
                        route_info = flight_routes_service.get_flight_route_info(
                            flight.icao24, 
                            flight.callsign
                        )
                        
                        # Korrekter Flight Status basierend auf on_ground
                        flight_status = "ground" if latest_pos.on_ground else "airborne"
                        
                        flight_info = {
                            'icao24': flight.icao24,
                            'callsign': flight.callsign or 'N/A',
                            'origin_country': flight.origin_country or 'Unknown',
                            'latitude': latest_pos.latitude,
                            'longitude': latest_pos.longitude,
                            'altitude': latest_pos.altitude,
                            'velocity': latest_pos.velocity,
                            'true_track': latest_pos.true_track,
                            'on_ground': latest_pos.on_ground,
                            'flight_status': flight_status,  # Korrigierter Status
                            'positions_count': len(flight.positions),
                            'last_seen': flight.last_seen,
                            'aircraft_info': flight.aircraft_info if hasattr(flight, 'aircraft_info') else None,
                            # Neue Route-Informationen
                            'route_info': {
                                'origin_city': route_info.origin_city if route_info else None,
                                'origin_country': route_info.origin_country if route_info else None,
                                'destination_city': route_info.destination_city if route_info else None,
                                'destination_country': route_info.destination_country if route_info else None,
                                'airline': route_info.airline if route_info else None,
                                'flight_number': route_info.flight_number if route_info else None
                            } if route_info else None
                        }
                        flight_data.append(flight_info)
                
                return jsonify({
                    'flights': flight_data,
                    'total_count': len(flight_data),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({'error': str(e)})
        
        @self.app.route('/api/flights/<icao24>/path')
        def get_flight_path(icao24):
            """API: Flugbahn für spezifisches Aircraft."""
            if not self.flight_tracker:
                return jsonify({'error': 'Flight Tracker nicht initialisiert'})
            
            try:
                flight = self.flight_tracker.flights.get(icao24)
                if not flight:
                    return jsonify({'error': 'Flight nicht gefunden'})
                
                # Flugbahn als Koordinaten-Array
                path = []
                for pos in flight.positions:
                    path.append({
                        'lat': pos.latitude,
                        'lng': pos.longitude,
                        'altitude': pos.altitude,
                        'timestamp': pos.timestamp,
                        'velocity': pos.velocity
                    })
                
                return jsonify({
                    'icao24': icao24,
                    'path': path,
                    'total_points': len(path)
                })
                
            except Exception as e:
                return jsonify({'error': str(e)})
        
        @self.app.route('/api/flights/filter/destination/<destination_country>')
        def get_flights_to_destination(destination_country):
            """API: Flüge nach bestimmtem Zielland."""
            if not self.flight_tracker:
                return jsonify({'error': 'Flight Tracker nicht initialisiert'})
            
            try:
                # Aktuelle Flüge holen
                active_flights = self.flight_tracker.get_active_flights()
                
                # Nach Zielland filtern
                filtered_flights = flight_routes_service.filter_flights_by_destination(
                    active_flights, destination_country
                )
                
                # Format für Karte
                flight_data = []
                for flight in filtered_flights:
                    if flight.positions:
                        latest_pos = flight.positions[-1]
                        route_info = flight.route_info if hasattr(flight, 'route_info') else None
                        
                        flight_info = {
                            'icao24': flight.icao24,
                            'callsign': flight.callsign or 'N/A',
                            'origin_country': flight.origin_country or 'Unknown',
                            'latitude': latest_pos.latitude,
                            'longitude': latest_pos.longitude,
                            'altitude': latest_pos.altitude,
                            'velocity': latest_pos.velocity,
                            'true_track': latest_pos.true_track,
                            'on_ground': latest_pos.on_ground,
                            'flight_status': "ground" if latest_pos.on_ground else "airborne",
                            'route_info': {
                                'origin_city': route_info.origin_city if route_info else None,
                                'origin_country': route_info.origin_country if route_info else None,
                                'destination_city': route_info.destination_city if route_info else None,
                                'destination_country': route_info.destination_country if route_info else None,
                                'airline': route_info.airline if route_info else None
                            } if route_info else None
                        }
                        flight_data.append(flight_info)
                
                return jsonify({
                    'flights': flight_data,
                    'total_count': len(flight_data),
                    'filter': f'destination: {destination_country}',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({'error': str(e)})
        
        @self.app.route('/api/flights/filter/origin/<origin_country>')
        def get_flights_from_origin(origin_country):
            """API: Flüge von bestimmtem Herkunftsland."""
            if not self.flight_tracker:
                return jsonify({'error': 'Flight Tracker nicht initialisiert'})
            
            try:
                # Aktuelle Flüge holen
                active_flights = self.flight_tracker.get_active_flights()
                
                # Nach Herkunftsland filtern
                filtered_flights = flight_routes_service.filter_flights_by_origin(
                    active_flights, origin_country
                )
                
                # Format für Karte
                flight_data = []
                for flight in filtered_flights:
                    if flight.positions:
                        latest_pos = flight.positions[-1]
                        route_info = flight.route_info if hasattr(flight, 'route_info') else None
                        
                        flight_info = {
                            'icao24': flight.icao24,
                            'callsign': flight.callsign or 'N/A',
                            'origin_country': flight.origin_country or 'Unknown',
                            'latitude': latest_pos.latitude,
                            'longitude': latest_pos.longitude,
                            'altitude': latest_pos.altitude,
                            'velocity': latest_pos.velocity,
                            'true_track': latest_pos.true_track,
                            'on_ground': latest_pos.on_ground,
                            'flight_status': "ground" if latest_pos.on_ground else "airborne",
                            'route_info': {
                                'origin_city': route_info.origin_city if route_info else None,
                                'origin_country': route_info.origin_country if route_info else None,
                                'destination_city': route_info.destination_city if route_info else None,
                                'destination_country': route_info.destination_country if route_info else None,
                                'airline': route_info.airline if route_info else None
                            } if route_info else None
                        }
                        flight_data.append(flight_info)
                
                return jsonify({
                    'flights': flight_data,
                    'total_count': len(flight_data),
                    'filter': f'origin: {origin_country}',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({'error': str(e)})
        
        @self.app.route('/api/flights/destinations')
        def get_available_destinations():
            """API: Alle verfügbaren Zielländer."""
            if not self.flight_tracker:
                return jsonify({'error': 'Flight Tracker nicht initialisiert'})
            
            try:
                active_flights = self.flight_tracker.get_active_flights()
                destinations = flight_routes_service.get_available_destinations(active_flights)
                
                return jsonify({
                    'destinations': destinations,
                    'count': len(destinations)
                })
                
            except Exception as e:
                return jsonify({'error': str(e)})
        
        @self.app.route('/api/flights/origins')
        def get_available_origins():
            """API: Alle verfügbaren Herkunftsländer."""
            if not self.flight_tracker:
                return jsonify({'error': 'Flight Tracker nicht initialisiert'})
            
            try:
                active_flights = self.flight_tracker.get_active_flights()
                origins = flight_routes_service.get_available_origins(active_flights)
                
                return jsonify({
                    'origins': origins,
                    'count': len(origins)
                })
                
            except Exception as e:
                return jsonify({'error': str(e)})
        
        @self.app.route('/api/flights/database/all')
        def get_all_database_flights():
            """API: Alle gespeicherten Flüge aus der Datenbank."""
            if not self.flight_tracker:
                return jsonify({'error': 'Flight Tracker nicht initialisiert'})
            
            try:
                # Hole alle Flüge aus der Datenbank
                all_flights = self.flight_tracker.get_all_stored_flights()
                
                # Anzahl berechnen
                total_count = len(all_flights)
                
                print(f" API: {total_count} gespeicherte Flüge aus DB abgerufen")
                
                return jsonify({
                    'success': True,
                    'flights': all_flights,
                    'total_count': total_count,
                    'message': f'{total_count} gespeicherte Flüge geladen'
                })
                
            except Exception as e:
                print(f"❌ Fehler beim Abrufen aller DB-Flüge: {e}")
                return jsonify({'error': f'Fehler beim Laden der Flüge: {str(e)}'})
        
        @self.app.route('/api/statistics')
        def get_statistics():
            """API: System-Statistiken."""
            if not self.flight_tracker:
                return jsonify({'error': 'Flight Tracker nicht initialisiert'})
            
            try:
                stats = self.flight_tracker.get_flight_statistics()
                dashboard = self.flight_tracker.get_database_dashboard()
                
                return jsonify({
                    'flight_stats': stats,
                    'dashboard_data': dashboard,
                    'live_updates_enabled': self.live_updates_enabled,
                    'update_interval': self.update_interval
                })
                
            except Exception as e:
                return jsonify({'error': str(e)})
        
        @self.app.route('/api/historical/<int:hours>')
        def get_historical_flights(hours):
            """API: Historische Flugdaten."""
            if not self.flight_tracker:
                return jsonify({'error': 'Flight Tracker nicht initialisiert'})
            
            try:
                historical = self.flight_tracker.get_historical_flights(hours)
                return jsonify({
                    'historical_flights': historical,
                    'timeframe_hours': hours,
                    'total_count': len(historical)
                })
                
            except Exception as e:
                return jsonify({'error': str(e)})
        
        @self.app.route('/api/control/live-updates', methods=['POST'])
        def control_live_updates():
            """API: Live-Updates ein/ausschalten."""
            data = request.get_json()
            enable = data.get('enable', False)
            
            if enable and not self.live_updates_enabled:
                self.start_live_updates()
            elif not enable and self.live_updates_enabled:
                self.stop_live_updates()
            
            return jsonify({
                'live_updates_enabled': self.live_updates_enabled,
                'message': f"Live-Updates {'aktiviert' if enable else 'deaktiviert'}"
            })
    
    def _setup_websocket_handlers(self):
        """Setup WebSocket-Handler."""
        
        @self.socketio.on('connect')
        def handle_connect():
            print("🔌 Client verbunden")
            emit('status', {'message': 'Verbunden mit Airtrack Server'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print("🔌 Client getrennt")
        
        @self.socketio.on('request_update')
        def handle_request_update():
            """Client fordert Update an."""
            self.emit_flight_update()
    
    def start_live_updates(self):
        """Startet automatische Live-Updates."""
        if self.live_updates_enabled:
            return
        
        self.live_updates_enabled = True
        self.update_thread = threading.Thread(target=self._live_update_loop, daemon=True)
        self.update_thread.start()
        print(f"🔄 Live-Updates gestartet (alle {self.update_interval}s)")
    
    def stop_live_updates(self):
        """Stoppt automatische Live-Updates."""
        self.live_updates_enabled = False
        if self.update_thread:
            self.update_thread.join(timeout=1)
        print("⏹ Live-Updates gestoppt")
    
    def _live_update_loop(self):
        """Live-Update Loop für automatische Datenaktualisierung."""
        while self.live_updates_enabled:
            try:
                # Neue Daten von OpenSky abrufen
                raw_data = fetch_opensky_data()
                if raw_data:
                    aircraft_list = self.data_processor.process_opensky_data(raw_data)
                    
                    # Filter für bessere Performance (nur fliegende Aircraft)
                    filtered_aircraft = self.data_processor.filter_aircraft(aircraft_list, {
                        'only_with_position': True,
                        'only_airborne': True
                    })[:100]  # Limit für Web-Performance
                    
                    # Flight Tracker aktualisieren
                    self.flight_tracker.update_flights(filtered_aircraft)
                    
                    # Update an alle verbundenen Clients senden
                    self.emit_flight_update()
                    
                    print(f"🔄 Live-Update: {len(filtered_aircraft)} Aircraft verarbeitet")
                
            except Exception as e:
                print(f"❌ Live-Update Fehler: {e}")
            
            # Warte bis zum nächsten Update
            time.sleep(self.update_interval)
    
    def emit_flight_update(self):
        """Sendet Flight-Update an alle verbundenen Clients."""
        try:
            # Aktuelle Flugdaten holen
            active_flights = self.flight_tracker.get_active_flights()
            
            flight_data = []
            for flight in active_flights:
                if flight.positions:
                    latest_pos = flight.positions[-1]
                    
                    flight_info = {
                        'icao24': flight.icao24,
                        'callsign': flight.callsign or 'N/A',
                        'latitude': latest_pos.latitude,
                        'longitude': latest_pos.longitude,
                        'altitude': latest_pos.altitude,
                        'velocity': latest_pos.velocity,
                        'true_track': latest_pos.true_track,
                        'on_ground': latest_pos.on_ground,
                        'flight_status': flight.flight_status
                    }
                    flight_data.append(flight_info)
            
            # WebSocket Update senden
            self.socketio.emit('flight_update', {
                'flights': flight_data,
                'timestamp': datetime.now().isoformat(),
                'total_count': len(flight_data)
            })
            
        except Exception as e:
            print(f"❌ WebSocket Update Fehler: {e}")
    
    def run(self):
        """Startet den Web Server."""
        if not self.initialize_airtrack():
            print("❌ Kann Airtrack nicht initialisieren - Server startet trotzdem")
        
        print(f" Starte Airtrack Web Server auf http://{self.host}:{self.port}")
        print(" Öffne die URL in deinem Browser für die interaktive Karte!")
        
        self.socketio.run(
            self.app,
            host=self.host,
            port=self.port,
            debug=self.debug,
            allow_unsafe_werkzeug=True
        )

if __name__ == "__main__":
    server = AirtrackWebServer(host='127.0.0.1', port=5000, debug=True)
    server.run()
