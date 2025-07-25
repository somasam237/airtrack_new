"""
Flight Routes Service
Erweitert Airtrack um Flugziel- und Herkunftsinformationen
"""

import requests
import json
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
import time

@dataclass
class FlightRoute:
    """Flugziel und Herkunftsinformationen"""
    icao24: str
    callsign: Optional[str] = None
    origin_airport: Optional[str] = None
    origin_city: Optional[str] = None
    origin_country: Optional[str] = None
    destination_airport: Optional[str] = None
    destination_city: Optional[str] = None
    destination_country: Optional[str] = None
    airline: Optional[str] = None
    aircraft_type: Optional[str] = None
    flight_number: Optional[str] = None
    last_updated: Optional[str] = None

class FlightRoutesService:
    """
    Service für Flugziel- und Herkunftsinformationen
    Nutzt mehrere APIs für umfassende Daten
    """
    
    def __init__(self):
        self.cache = {}  # Cache für API-Antworten
        self.cache_duration = 3600  # 1 Stunde Cache
        
        # API Endpoints (kostenlose Services)
        self.aviationstack_api = "http://api.aviationstack.com/v1/flights"
        self.openflights_api = "https://openflights.org/php/apsearch.php"
        
        # Flughafen-Datenbank (statisch für bessere Performance)
        self.airport_db = self._load_airport_database()
        
        # Länder-Mapping für bessere Filterung
        self.country_mapping = {
            'Germany': ['DE', 'DEU', 'Deutschland'],
            'United States': ['US', 'USA', 'United States'],
            'France': ['FR', 'FRA', 'France', 'Frankreich'],
            'United Kingdom': ['GB', 'GBR', 'UK', 'England'],
            'Spain': ['ES', 'ESP', 'Spain', 'Spanien'],
            'Italy': ['IT', 'ITA', 'Italy', 'Italien'],
            'Netherlands': ['NL', 'NLD', 'Netherlands', 'Niederlande'],
            'Switzerland': ['CH', 'CHE', 'Switzerland', 'Schweiz'],
            'Austria': ['AT', 'AUT', 'Austria', 'Österreich'],
            # NEUE AFRIKANISCHE LÄNDER
            'Cameroon': ['CM', 'CMR', 'Cameroon', 'Kamerun'],
            'Nigeria': ['NG', 'NGA', 'Nigeria'],
            'South Africa': ['ZA', 'ZAF', 'South Africa', 'Südafrika'],
            'Kenya': ['KE', 'KEN', 'Kenya', 'Kenia'],
            'Ethiopia': ['ET', 'ETH', 'Ethiopia', 'Äthiopien'],
            'Ghana': ['GH', 'GHA', 'Ghana'],
            'Morocco': ['MA', 'MAR', 'Morocco', 'Marokko'],
            'Egypt': ['EG', 'EGY', 'Egypt', 'Ägypten']
        }
    
    def _load_airport_database(self) -> Dict[str, Any]:
        """Laedt eine statische Flughafen-Datenbank"""
        # Wichtige deutsche und europäische Flughäfen
        airports = {
            'EDDF': {'city': 'Frankfurt', 'country': 'Germany', 'name': 'Frankfurt Airport'},
            'EDDM': {'city': 'München', 'country': 'Germany', 'name': 'Munich Airport'},
            'EDDB': {'city': 'Berlin', 'country': 'Germany', 'name': 'Berlin Brandenburg'},
            'EDDH': {'city': 'Hamburg', 'country': 'Germany', 'name': 'Hamburg Airport'},
            'EDDL': {'city': 'Düsseldorf', 'country': 'Germany', 'name': 'Düsseldorf Airport'},
            'EDDS': {'city': 'Stuttgart', 'country': 'Germany', 'name': 'Stuttgart Airport'},
            'EDDV': {'city': 'Hannover', 'country': 'Germany', 'name': 'Hannover Airport'},
            
            'LFPG': {'city': 'Paris', 'country': 'France', 'name': 'Charles de Gaulle'},
            'EGLL': {'city': 'London', 'country': 'United Kingdom', 'name': 'Heathrow'},
            'EHAM': {'city': 'Amsterdam', 'country': 'Netherlands', 'name': 'Schiphol'},
            'LSZH': {'city': 'Zürich', 'country': 'Switzerland', 'name': 'Zurich Airport'},
            'LOWW': {'city': 'Wien', 'country': 'Austria', 'name': 'Vienna Airport'},
            'LEMD': {'city': 'Madrid', 'country': 'Spain', 'name': 'Madrid Barajas'},
            'LIRF': {'city': 'Rom', 'country': 'Italy', 'name': 'Rome Fiumicino'},
            'LIRN': {'city': 'Neapel', 'country': 'Italy', 'name': 'Naples Airport'},
            
            'KJFK': {'city': 'New York', 'country': 'United States', 'name': 'JFK Airport'},
            'KLAX': {'city': 'Los Angeles', 'country': 'United States', 'name': 'LAX Airport'},
            'KORD': {'city': 'Chicago', 'country': 'United States', 'name': 'O\'Hare Airport'},
            
            # NEUE AFRIKANISCHE FLUGHÄFEN
            'FKYS': {'city': 'Yaoundé', 'country': 'Cameroon', 'name': 'Yaoundé Nsimalen Airport'},
            'FKKD': {'city': 'Douala', 'country': 'Cameroon', 'name': 'Douala Airport'},
            'DNMM': {'city': 'Lagos', 'country': 'Nigeria', 'name': 'Murtala Muhammed Airport'},
            'DNAA': {'city': 'Abuja', 'country': 'Nigeria', 'name': 'Nnamdi Azikiwe Airport'},
            'FAOR': {'city': 'Johannesburg', 'country': 'South Africa', 'name': 'OR Tambo Airport'},
            'FACT': {'city': 'Cape Town', 'country': 'South Africa', 'name': 'Cape Town Airport'},
            'FADN': {'city': 'Durban', 'country': 'South Africa', 'name': 'King Shaka Airport'},
        }
        return airports
    
    def get_flight_route_info(self, icao24: str, callsign: Optional[str] = None) -> Optional[FlightRoute]:
        """
        Holt Flugziel-Informationen für ein Aircraft Returns: FlightRoute object mit Ziel/Herkunft oder None
        """
        # Cache prüfen
        cache_key = f"{icao24}_{callsign}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                return cached_data
        
        # Verschiedene Methoden versuchen
        route_info = None
        
        # 1. Versuche mit Callsign-Analyse
        if callsign:
            route_info = self._analyze_callsign(icao24, callsign)
        
        # 2. Versuche mit ICAO24-Analyse (Länder-Mapping)
        if not route_info:
            route_info = self._analyze_icao24(icao24, callsign)
        
        # 3. Dummy-Daten für Demo (entfernen in Production)
        if not route_info:
            route_info = self._generate_demo_route(icao24, callsign)
        
        # Cache speichern
        if route_info:
            self.cache[cache_key] = (route_info, time.time())
        
        return route_info
    
    def _analyze_callsign(self, icao24: str, callsign: str) -> Optional[FlightRoute]:
        """Analysiert Callsign fuer Airline und moegliche Routen"""
        if not callsign or len(callsign) < 2:
            return None
        
        # Airline-Mapping basierend auf Callsign-Prefix
        airline_mapping = {
            'DLH': {'airline': 'Lufthansa', 'country': 'Germany', 'hub': 'Frankfurt'},
            'AFR': {'airline': 'Air France', 'country': 'France', 'hub': 'Paris'},
            'BAW': {'airline': 'British Airways', 'country': 'United Kingdom', 'hub': 'London'},
            'KLM': {'airline': 'KLM', 'country': 'Netherlands', 'hub': 'Amsterdam'},
            'SWR': {'airline': 'Swiss', 'country': 'Switzerland', 'hub': 'Zürich'},
            'AUA': {'airline': 'Austrian Airlines', 'country': 'Austria', 'hub': 'Wien'},
            'IBE': {'airline': 'Iberia', 'country': 'Spain', 'hub': 'Madrid'},
            'AZA': {'airline': 'Alitalia', 'country': 'Italy', 'hub': 'Rom'},
            'UAL': {'airline': 'United Airlines', 'country': 'United States', 'hub': 'Chicago'},
            'AAL': {'airline': 'American Airlines', 'country': 'United States', 'hub': 'Dallas'},
            'EZY': {'airline': 'EasyJet', 'country': 'United Kingdom', 'hub': 'London'},
            'RYR': {'airline': 'Ryanair', 'country': 'Ireland', 'hub': 'Dublin'},
            # NEUE AFRIKANISCHE AIRLINES
            'CAM': {'airline': 'Camair-Co', 'country': 'Cameroon', 'hub': 'Douala'},
            'ADK': {'airline': 'Air Afrique', 'country': 'Cameroon', 'hub': 'Yaoundé'},
            'NGA': {'airline': 'Air Nigeria', 'country': 'Nigeria', 'hub': 'Lagos'},
            'ABC': {'airline': 'Arik Air', 'country': 'Nigeria', 'hub': 'Lagos'},
            'SAA': {'airline': 'South African Airways', 'country': 'South Africa', 'hub': 'Johannesburg'},
            'MNO': {'airline': 'Mango Airlines', 'country': 'South Africa', 'hub': 'Johannesburg'},
            'CUL': {'airline': 'Kulula.com', 'country': 'South Africa', 'hub': 'Johannesburg'},
            'FLY': {'airline': 'FlySafair', 'country': 'South Africa', 'hub': 'Johannesburg'},
        }
        
        # Callsign-Prefix analysieren
        prefix = callsign[:3].upper()
        if prefix in airline_mapping:
            airline_info = airline_mapping[prefix]
            
            return FlightRoute(
                icao24=icao24,
                callsign=callsign,
                airline=airline_info['airline'],
                origin_country=airline_info['country'],
                origin_city=airline_info['hub'],
                # Ziel basierend auf typischen Routen schätzen
                destination_country='Germany' if airline_info['country'] != 'Germany' else 'Various',
                last_updated=time.strftime('%Y-%m-%d %H:%M:%S')
            )
        
        return None
    
    def _analyze_icao24(self, icao24: str, callsign: Optional[str]) -> Optional[FlightRoute]:
        """Analysiert ICAO24 für Herkunftsland"""
        if not icao24 or len(icao24) < 6:
            return None
        
        # ICAO24 Länder-Prefixes
        icao_country_mapping = {
            '3': 'United States',
            '4': 'Germany', 
            '5': 'Germany',
            '6': 'Germany',
            '7': 'Germany',
            'F-': 'France',
            'G-': 'United Kingdom',
            'PH-': 'Netherlands',
            'HB-': 'Switzerland',
            'OE-': 'Austria',
            'EC-': 'Spain',
            'I-': 'Italy'
        }
        
        # Prefix bestimmen
        prefix = icao24[:1].upper() if len(icao24) >= 1 else ''
        country = icao_country_mapping.get(prefix)
        
        if country:
            return FlightRoute(
                icao24=icao24,
                callsign=callsign,
                origin_country=country,
                last_updated=time.strftime('%Y-%m-%d %H:%M:%S')
            )
        
        return None
    
    def _generate_demo_route(self, icao24: str, callsign: Optional[str]) -> FlightRoute:
        """Generiert Demo-Routendaten fuer Testzwecke"""
        import random
        
        # Zufällige Demo-Routen
        demo_routes = [
            {
                'origin_city': 'Frankfurt', 'origin_country': 'Germany',
                'destination_city': 'Paris', 'destination_country': 'France',
                'airline': 'Lufthansa'
            },
            {
                'origin_city': 'London', 'origin_country': 'United Kingdom',
                'destination_city': 'München', 'destination_country': 'Germany',
                'airline': 'British Airways'
            },
            {
                'origin_city': 'Amsterdam', 'origin_country': 'Netherlands',
                'destination_city': 'Berlin', 'destination_country': 'Germany',
                'airline': 'KLM'
            },
            {
                'origin_city': 'Madrid', 'origin_country': 'Spain',
                'destination_city': 'Hamburg', 'destination_country': 'Germany',
                'airline': 'Iberia'
            },
            {
                'origin_city': 'New York', 'origin_country': 'United States',
                'destination_city': 'Frankfurt', 'destination_country': 'Germany',
                'airline': 'United Airlines'
            },
            # NEUE AFRIKANISCHE ROUTEN
            {
                'origin_city': 'Douala', 'origin_country': 'Cameroon',
                'destination_city': 'Frankfurt', 'destination_country': 'Germany',
                'airline': 'Camair-Co'
            },
            {
                'origin_city': 'Paris', 'origin_country': 'France',
                'destination_city': 'Yaoundé', 'destination_country': 'Cameroon',
                'airline': 'Air France'
            },
            {
                'origin_city': 'Lagos', 'origin_country': 'Nigeria',
                'destination_city': 'London', 'destination_country': 'United Kingdom',
                'airline': 'British Airways'
            },
            {
                'origin_city': 'Amsterdam', 'origin_country': 'Netherlands',
                'destination_city': 'Lagos', 'destination_country': 'Nigeria',
                'airline': 'KLM'
            },
            {
                'origin_city': 'Johannesburg', 'origin_country': 'South Africa',
                'destination_city': 'Frankfurt', 'destination_country': 'Germany',
                'airline': 'South African Airways'
            },
            {
                'origin_city': 'London', 'origin_country': 'United Kingdom',
                'destination_city': 'Cape Town', 'destination_country': 'South Africa',
                'airline': 'British Airways'
            },
            {
                'origin_city': 'Düsseldorf', 'origin_country': 'Germany',
                'destination_city': 'Johannesburg', 'destination_country': 'South Africa',
                'airline': 'Lufthansa'
            }
        ]
        
        route = random.choice(demo_routes)
        
        return FlightRoute(
            icao24=icao24,
            callsign=callsign,
            origin_city=route['origin_city'],
            origin_country=route['origin_country'],
            destination_city=route['destination_city'],
            destination_country=route['destination_country'],
            airline=route['airline'],
            last_updated=time.strftime('%Y-%m-%d %H:%M:%S')
        )
    
    def filter_flights_by_destination(self, flights: List[Any], destination_country: str) -> List[Any]:
        """
        Filtert Flüge nach Zielland Returns: Gefilterte Liste von Flügen
        """
        filtered_flights = []
        
        for flight in flights:
            route_info = self.get_flight_route_info(flight.icao24, flight.callsign)
            if route_info and route_info.destination_country:
                # Flexibles Matching mit Country-Mapping
                if self._country_matches(route_info.destination_country, destination_country):
                    # Route-Info zum Flight hinzufügen
                    flight.route_info = route_info
                    filtered_flights.append(flight)
        
        return filtered_flights
    
    def filter_flights_by_origin(self, flights: List[Any], origin_country: str) -> List[Any]:
        """Filtert Fluege nach Herkunftsland"""
        filtered_flights = []
        
        for flight in flights:
            route_info = self.get_flight_route_info(flight.icao24, flight.callsign)
            if route_info and route_info.origin_country:
                if self._country_matches(route_info.origin_country, origin_country):
                    flight.route_info = route_info
                    filtered_flights.append(flight)
        
        return filtered_flights
    
    def _country_matches(self, country1: str, country2: str) -> bool:
        """Prueft ob zwei Laendernamen uebereinstimmen (flexibel)"""
        if not country1 or not country2:
            return False
        
        # Direkte Übereinstimmung
        if country1.lower() == country2.lower():
            return True
        
        # Mapping-basierte Übereinstimmung
        for canonical, variants in self.country_mapping.items():
            if (country1 in variants or country1 == canonical) and \
               (country2 in variants or country2 == canonical):
                return True
        
        return False
    
    def get_available_destinations(self, flights: List[Any]) -> List[str]:
        """Gibt alle verfuegbaren Ziellaender zurueck"""
        destinations = set()
        
        for flight in flights:
            route_info = self.get_flight_route_info(flight.icao24, flight.callsign)
            if route_info and route_info.destination_country:
                destinations.add(route_info.destination_country)
        
        return sorted(list(destinations))
    
    def get_available_origins(self, flights: List[Any]) -> List[str]:
        """Gibt alle verfuegbaren Herkunftslaender zurueck"""
        origins = set()
        
        for flight in flights:
            route_info = self.get_flight_route_info(flight.icao24, flight.callsign)
            if route_info and route_info.origin_country:
                origins.add(route_info.origin_country)
        
        return sorted(list(origins))

# Globale Instanz für einfache Nutzung
flight_routes_service = FlightRoutesService()
