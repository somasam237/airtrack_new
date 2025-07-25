import requests
import time
from datetime import datetime
from data_processor import DataProcessor, Aircraft
from typing import List, Dict, Any
import random

def generate_test_flight_data():
    """Generiert realistische Testflugdaten für Europa und Afrika."""
    test_flights = []
    
    # Europäische und afrikanische Flughäfen mit realistischen Koordinaten
    airports = [
        # Deutschland
        {"name": "Frankfurt", "lat": 50.033, "lon": 8.570, "country": "Germany", "iata": "FRA"},
        {"name": "Munich", "lat": 48.354, "lon": 11.786, "country": "Germany", "iata": "MUC"},
        {"name": "Berlin", "lat": 52.560, "lon": 13.288, "country": "Germany", "iata": "BER"},
        {"name": "Hamburg", "lat": 53.630, "lon": 9.988, "country": "Germany", "iata": "HAM"},
        {"name": "Düsseldorf", "lat": 51.289, "lon": 6.767, "country": "Germany", "iata": "DUS"},
        
        # Frankreich
        {"name": "Paris CDG", "lat": 49.013, "lon": 2.550, "country": "France", "iata": "CDG"},
        {"name": "Paris Orly", "lat": 48.723, "lon": 2.379, "country": "France", "iata": "ORY"},
        {"name": "Lyon", "lat": 45.726, "lon": 5.081, "country": "France", "iata": "LYS"},
        {"name": "Nice", "lat": 43.658, "lon": 7.216, "country": "France", "iata": "NCE"},
        
        # Großbritannien
        {"name": "London Heathrow", "lat": 51.470, "lon": -0.454, "country": "United Kingdom", "iata": "LHR"},
        {"name": "London Gatwick", "lat": 51.148, "lon": -0.190, "country": "United Kingdom", "iata": "LGW"},
        {"name": "Manchester", "lat": 53.365, "lon": -2.273, "country": "United Kingdom", "iata": "MAN"},
        
        # Italien
        {"name": "Rome Fiumicino", "lat": 41.800, "lon": 12.250, "country": "Italy", "iata": "FCO"},
        {"name": "Milan Malpensa", "lat": 45.630, "lon": 8.728, "country": "Italy", "iata": "MXP"},
        {"name": "Venice", "lat": 45.505, "lon": 12.352, "country": "Italy", "iata": "VCE"},
        
        # Spanien
        {"name": "Madrid", "lat": 40.472, "lon": -3.561, "country": "Spain", "iata": "MAD"},
        {"name": "Barcelona", "lat": 41.297, "lon": 2.078, "country": "Spain", "iata": "BCN"},
        {"name": "Palma", "lat": 39.551, "lon": 2.739, "country": "Spain", "iata": "PMI"},
        
        # Niederlande
        {"name": "Amsterdam", "lat": 52.308, "lon": 4.764, "country": "Netherlands", "iata": "AMS"},
        
        # Schweiz
        {"name": "Zurich", "lat": 47.464, "lon": 8.549, "country": "Switzerland", "iata": "ZUR"},
        {"name": "Geneva", "lat": 46.238, "lon": 6.109, "country": "Switzerland", "iata": "GVA"},
        
        # Österreich
        {"name": "Vienna", "lat": 48.110, "lon": 16.570, "country": "Austria", "iata": "VIE"},
        
        # Nordafrika
        {"name": "Cairo", "lat": 30.122, "lon": 31.406, "country": "Egypt", "iata": "CAI"},
        {"name": "Casablanca", "lat": 33.367, "lon": -7.590, "country": "Morocco", "iata": "CMN"},
        {"name": "Tunis", "lat": 36.851, "lon": 10.227, "country": "Tunisia", "iata": "TUN"},
        {"name": "Algiers", "lat": 36.691, "lon": 3.215, "country": "Algeria", "iata": "ALG"},
        
        # Westafrika
        {"name": "Douala", "lat": 4.006, "lon": 9.719, "country": "Cameroon", "iata": "DLA"},
        {"name": "Yaoundé", "lat": 3.836, "lon": 11.524, "country": "Cameroon", "iata": "YAO"},
        {"name": "Lagos", "lat": 6.577, "lon": 3.321, "country": "Nigeria", "iata": "LOS"},
        {"name": "Abuja", "lat": 9.007, "lon": 7.263, "country": "Nigeria", "iata": "ABV"},
        {"name": "Accra", "lat": 5.605, "lon": -0.167, "country": "Ghana", "iata": "ACC"},
        {"name": "Dakar", "lat": 14.740, "lon": -17.490, "country": "Senegal", "iata": "DKR"},
        {"name": "Abidjan", "lat": 5.261, "lon": -3.926, "country": "Ivory Coast", "iata": "ABJ"},
        
        # Ostafrika
        {"name": "Addis Ababa", "lat": 8.978, "lon": 38.799, "country": "Ethiopia", "iata": "ADD"},
        {"name": "Nairobi", "lat": -1.319, "lon": 36.928, "country": "Kenya", "iata": "NBO"},
        {"name": "Dar es Salaam", "lat": -6.878, "lon": 39.203, "country": "Tanzania", "iata": "DAR"},
        {"name": "Kigali", "lat": -1.968, "lon": 30.139, "country": "Rwanda", "iata": "KGL"},
        
        # Südafrika
        {"name": "Johannesburg", "lat": -26.139, "lon": 28.246, "country": "South Africa", "iata": "JNB"},
        {"name": "Cape Town", "lat": -33.965, "lon": 18.602, "country": "South Africa", "iata": "CPT"},
        {"name": "Durban", "lat": -29.970, "lon": 30.951, "country": "South Africa", "iata": "DUR"},
        
        # Osteuropa
        {"name": "Warsaw", "lat": 52.166, "lon": 20.967, "country": "Poland", "iata": "WAW"},
        {"name": "Prague", "lat": 50.101, "lon": 14.260, "country": "Czech Republic", "iata": "PRG"},
        {"name": "Budapest", "lat": 47.437, "lon": 19.255, "country": "Hungary", "iata": "BUD"},
        {"name": "Moscow", "lat": 55.973, "lon": 37.415, "country": "Russia", "iata": "SVO"},
        
        # Skandinavien
        {"name": "Stockholm", "lat": 59.650, "lon": 17.918, "country": "Sweden", "iata": "ARN"},
        {"name": "Copenhagen", "lat": 55.618, "lon": 12.656, "country": "Denmark", "iata": "CPH"},
        {"name": "Oslo", "lat": 60.202, "lon": 11.084, "country": "Norway", "iata": "OSL"},
    ]
    
    # Realistische Airlines
    airlines = [
        {"code": "LH", "name": "Lufthansa", "country": "Germany"},
        {"code": "AF", "name": "Air France", "country": "France"},
        {"code": "BA", "name": "British Airways", "country": "United Kingdom"},
        {"code": "KL", "name": "KLM", "country": "Netherlands"},
        {"code": "IB", "name": "Iberia", "country": "Spain"},
        {"code": "LX", "name": "Swiss International", "country": "Switzerland"},
        {"code": "OS", "name": "Austrian Airlines", "country": "Austria"},
        {"code": "AZ", "name": "Alitalia", "country": "Italy"},
        {"code": "SN", "name": "Brussels Airlines", "country": "Belgium"},
        {"code": "TP", "name": "TAP Portugal", "country": "Portugal"},
        {"code": "MS", "name": "EgyptAir", "country": "Egypt"},
        {"code": "AT", "name": "Royal Air Maroc", "country": "Morocco"},
        {"code": "TU", "name": "Tunisair", "country": "Tunisia"},
        {"code": "AH", "name": "Air Algérie", "country": "Algeria"},
        {"code": "UY", "name": "Cameroon Airlines", "country": "Cameroon"},
        {"code": "QC", "name": "Camair-Co", "country": "Cameroon"},
        {"code": "W3", "name": "Arik Air", "country": "Nigeria"},
        {"code": "WA", "name": "KLM Cityhopper", "country": "Ghana"},
        {"code": "HC", "name": "Air Senegal", "country": "Senegal"},
        {"code": "HF", "name": "Air Côte d'Ivoire", "country": "Ivory Coast"},
        {"code": "ET", "name": "Ethiopian Airlines", "country": "Ethiopia"},
        {"code": "KQ", "name": "Kenya Airways", "country": "Kenya"},
        {"code": "TC", "name": "Air Tanzania", "country": "Tanzania"},
        {"code": "WB", "name": "RwandAir", "country": "Rwanda"},
        {"code": "SA", "name": "South African Airways", "country": "South Africa"},
        {"code": "MN", "name": "Kulula.com", "country": "South Africa"},
        {"code": "LO", "name": "LOT Polish Airlines", "country": "Poland"},
        {"code": "OK", "name": "Czech Airlines", "country": "Czech Republic"},
        {"code": "SU", "name": "Aeroflot", "country": "Russia"},
        {"code": "SK", "name": "SAS", "country": "Sweden"},
        {"code": "DY", "name": "Norwegian Air", "country": "Norway"},
    ]
    
    # Generiere 50 realistische Flüge
    for i in range(50):
        # Zufälliger ICAO24 Code
        icao24 = f"{''.join(random.choices('0123456789ABCDEF', k=6))}"
        
        # Zufällige Airline
        airline = random.choice(airlines)
        flight_number = f"{airline['code']}{random.randint(100, 9999)}"
        
        # Zufällige Route (Start und Ziel)
        origin = random.choice(airports)
        destination = random.choice([a for a in airports if a != origin])
        
        # Flugposition zwischen Start und Ziel interpolieren
        # 0.0 = am Start, 1.0 = am Ziel
        progress = random.uniform(0.1, 0.9)
        lat = origin["lat"] + (destination["lat"] - origin["lat"]) * progress
        lon = origin["lon"] + (destination["lon"] - origin["lon"]) * progress
        
        # Zufällige Flugdaten
        altitude = random.choice([
            random.randint(0, 1000),     # Am Boden oder Start/Landung
            random.randint(8000, 12000)  # Reiseflughöhe
        ])
        
        on_ground = altitude < 1000
        velocity = random.randint(150, 900) if not on_ground else random.randint(0, 50)
        true_track = random.randint(0, 359)
        
        flight_data = {
            'icao24': icao24,
            'callsign': flight_number,
            'origin_country': origin["country"],
            'time_position': int(time.time()),
            'last_contact': int(time.time()),
            'longitude': round(lon, 6),
            'latitude': round(lat, 6),
            'baro_altitude': altitude if not on_ground else None,
            'on_ground': on_ground,
            'velocity': velocity,
            'true_track': true_track,
            'vertical_rate': random.uniform(-5, 5) if not on_ground else 0,
            'sensors': None,
            'geo_altitude': altitude if not on_ground else None,
            'squawk': f"{random.randint(1000, 7777):04d}",
            'spi': False,
            'position_source': 0,
            # Zusätzliche Routeninformationen
            'origin_airport': origin,
            'destination_airport': destination,
            'airline_info': airline,
            'flight_progress': progress
        }
        
        test_flights.append(flight_data)
    
    return test_flights


def fetch_opensky_data():
    """
    Ruft Live-Flugdaten von der OpenSky Network API ab.
    Mit verbesserter Rate-Limiting-Behandlung und regionaler Filterung.
    """
    # Regionale Bounding Box für Europa und Afrika
    # min_longitude, min_latitude, max_longitude, max_latitude
    europe_africa_bbox = "-20,30,50,70"  # Europa + Nordafrika
    
    # URLs mit regionaler Filterung
    urls_to_try = [
        f"https://opensky-network.org/api/states/all?lamin=30&lomin=-20&lamax=70&lomax=50",  # Europa/Afrika
        "https://opensky-network.org/api/states/all"  # Weltweite Daten als Fallback
    ]
    
    headers = {
        'User-Agent': 'Airtrack Flight Tracker 1.0',
        'Accept': 'application/json',
    }
    
    for i, url in enumerate(urls_to_try):
        try:
            print(f"📡 Versuche API-Aufruf {i+1}/{len(urls_to_try)}...")
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 429:  # Rate Limited
                print("⏱️ Rate Limit erreicht, warte 60 Sekunden...")
                time.sleep(60)
                continue
            
            response.raise_for_status()
            data = response.json()
            
            if data and data.get('states'):
                # Filtern nach Europa/Afrika falls das erste URL fehlschlug
                if i > 0:  # Falls weltweite API verwendet wurde
                    filtered_states = []
                    for state in data['states']:
                        if state[6] and state[5]:  # latitude, longitude
                            lat, lon = state[6], state[5]
                            # Europa und Afrika Bereich
                            if 30 <= lat <= 70 and -20 <= lon <= 50:
                                filtered_states.append(state)
                    data['states'] = filtered_states
                
                data['fetch_time'] = datetime.now().isoformat()
                data['source'] = 'opensky_api'
                print(f"✅ Live-Daten: {len(data.get('states', []))} Flugzeuge von OpenSky API")
                return data
            else:
                print("⚠️ Keine Flugdaten von API erhalten")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️ OpenSky API Fehler (Versuch {i+1}): {e}")
            if i < len(urls_to_try) - 1:
                print("🔄 Versuche nächste URL...")
                time.sleep(5)
            continue
    
    # Fallback auf erweiterte lokale Testdaten
    print("🔄 Verwende erweiterte lokale Testdaten...")
    test_data = generate_realistic_flight_data()
    
    print(f"✅ Test-Daten: {len(test_data)} Flugzeuge generiert")
    return {
        'time': int(time.time()),
        'states': test_data,
        'fetch_time': datetime.now().isoformat(),
        'source': 'test_data'
    }

def generate_realistic_flight_data():
    """Generiert realistische Flugdaten im OpenSky API Format."""
    test_flights = generate_test_flight_data()
    
    # Konvertiere zu OpenSky State Vector Format
    state_vectors = []
    for flight in test_flights:
        state_vector = [
            flight['icao24'],                    # 0: icao24
            flight['callsign'],                  # 1: callsign  
            flight['origin_country'],            # 2: origin_country
            flight['time_position'],             # 3: time_position
            flight['last_contact'],              # 4: last_contact
            flight['longitude'],                 # 5: longitude
            flight['latitude'],                  # 6: latitude
            flight['baro_altitude'],             # 7: baro_altitude
            flight['on_ground'],                 # 8: on_ground
            flight['velocity'],                  # 9: velocity
            flight['true_track'],                # 10: true_track
            flight.get('vertical_rate'),         # 11: vertical_rate
            flight.get('sensors'),               # 12: sensors
            flight.get('geo_altitude'),          # 13: geo_altitude
            flight.get('squawk'),                # 14: squawk
            flight.get('spi', False),            # 15: spi
            flight.get('position_source', 0)     # 16: position_source
        ]
        state_vectors.append(state_vector)
    
    return state_vectors

def live_data_collector_with_processing(interval_seconds=10, 
                                      save_to_file=False,
                                      filters=None):
    """
    Sammelt kontinuierlich Live-Flugdaten mit Datenverarbeitung.
    
    Args:
        interval_seconds (int): Abrufintervall in Sekunden
        save_to_file (bool): Speichert Daten in JSON-Dateien
        filters (dict): Filterkriterien für Flugzeuge
    """
    print(f"Starte erweiterten Live-Datenabruf alle {interval_seconds} Sekunden...")
    print("Features: Datenverarbeitung, Statistiken, Filterung")
    if save_to_file:
        print("✓ Speichert Daten in JSON-Dateien")
    print("Drücken Sie Ctrl+C zum Stoppen\n")
    
    processor = DataProcessor()
    iteration = 0
    
    try:
        while True:
            iteration += 1
            print(f"--- Iteration {iteration} ---")
            
            # 1. Daten abrufen
            raw_data = fetch_opensky_data()
            if not raw_data:
                print("❌ Keine Daten erhalten, warte bis zum nächsten Versuch...")
                time.sleep(interval_seconds)
                continue
            
            # 2. Daten verarbeiten
            aircraft_list = processor.process_opensky_data(raw_data)
            
            # 3. Filter anwenden (falls vorhanden)
            if filters:
                aircraft_list = processor.filter_aircraft(aircraft_list, filters)
                print(f"✓ Nach Filterung: {len(aircraft_list)} Flugzeuge")
            
            # 4. Statistiken berechnen und anzeigen
            stats = processor.get_statistics(aircraft_list)
            print(f"✓ Total: {stats['total_aircraft']} | "
                  f"Fliegend: {stats['airborne']} | "
                  f"Am Boden: {stats['on_ground']} | "
                  f"Mit Position: {stats['with_position']}")
            
            if stats['avg_altitude']:
                print(f"✓ Durchschnittshöhe: {stats['avg_altitude']:.0f}m | "
                      f"Max: {stats['max_altitude']:.0f}m | "
                      f"Länder: {stats['country_count']}")
            
            # 5. Daten speichern (optional)
            if save_to_file and aircraft_list:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"airtrack_data_{timestamp}.json"
                processor.export_to_json(aircraft_list, filename)
                print(f"✓ Daten gespeichert: {filename}")
            
            print(f"⏱ Warte {interval_seconds} Sekunden...\n")
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print(f"\n🛑 Live-Datenabruf gestoppt nach {iteration} Iterationen")
        print(f"📊 Verarbeitungsstatistiken:")
        print(f"   Verarbeitet: {processor.processed_count}")
        print(f"   Fehler: {processor.error_count}")

def analyze_current_flights():
    """Analysiert die aktuellen Flüge mit verschiedenen Filtern."""
    print("=== FLUGANALYSE ===")
    
    # Daten abrufen und verarbeiten
    raw_data = fetch_opensky_data()
    if not raw_data:
        print("❌ Keine Daten verfügbar!")
        return
    
    processor = DataProcessor()
    all_aircraft = processor.process_opensky_data(raw_data)
    
    print(f"\n📊 GESAMTSTATISTIKEN:")
    stats = processor.get_statistics(all_aircraft)
    for key, value in stats.items():
        if key != 'countries' and key != 'processing_stats':
            print(f"   {key}: {value}")
    
    # Verschiedene Analysen
    analyses = [
        {
            'name': 'Hochfliegende Flugzeuge (>10.000m)',
            'filters': {'only_airborne': True, 'min_altitude': 10000}
        },
        {
            'name': 'Schnelle Flugzeuge (>800 km/h)', 
            'filters': {'only_airborne': True},
            'post_filter': lambda a: a.get_speed_kmh() and a.get_speed_kmh() > 800
        },
        {
            'name': 'Deutsche Flugzeuge',
            'filters': {'country': 'Germany'}
        },
        {
            'name': 'US-Amerikanische Flugzeuge',
            'filters': {'country': 'United States'}
        },
        {
            'name': 'Flugzeuge am Boden',
            'filters': {'only_airborne': False}
        }
    ]
    
    print(f"\n🔍 DETAILANALYSEN:")
    for analysis in analyses:
        filtered = processor.filter_aircraft(all_aircraft, analysis['filters'])
        
        # Post-Filter anwenden (für komplexere Bedingungen)
        if 'post_filter' in analysis:
            filtered = [a for a in filtered if analysis['post_filter'](a)]
        
        print(f"   {analysis['name']}: {len(filtered)} Flugzeuge")
        
        # Zeige Beispiele
        if filtered and len(filtered) <= 5:
            for aircraft in filtered[:3]:
                callsign = aircraft.callsign or "N/A"
                country = aircraft.origin_country or "N/A"
                print(f"     - {aircraft.icao24} ({callsign}) aus {country}")

if __name__ == "__main__":
    print("=== AIRTRACK DATENVERARBEITUNG ===")
    print("Was möchten Sie testen?")
    print("1. Einzelne Analyse der aktuellen Flüge")
    print("2. Live-Datenabruf mit Verarbeitung (einfach)")
    print("3. Live-Datenabruf mit Verarbeitung + Speicherung")
    print("4. Live-Datenabruf nur für deutsche Flugzeuge")
    print("5. Live-Datenabruf nur für Hochfliegende (>5000m)")
    
    choice = input("\nWählen Sie (1-5): ").strip()
    
    if choice == "1":
        analyze_current_flights()
    elif choice == "2":
        live_data_collector_with_processing(10, save_to_file=False)
    elif choice == "3":
        live_data_collector_with_processing(15, save_to_file=True)
    elif choice == "4":
        filters = {'country': 'Germany', 'only_with_position': True}
        live_data_collector_with_processing(10, filters=filters)
    elif choice == "5":
        filters = {'only_airborne': True, 'min_altitude': 5000, 'only_with_position': True}
        live_data_collector_with_processing(10, filters=filters)
    else:
        print("Ungültige Auswahl. Führe Standardanalyse aus...")
        analyze_current_flights()
