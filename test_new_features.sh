#!/bin/bash
# Test-Script für die neuen Airtrack-Funktionen

echo "🧪 AIRTRACK ERWEITERUNGS-TEST"
echo "================================="

# 1. Test der neuen API-Endpunkte
echo "📡 Teste neue API-Endpunkte..."

echo "1. Teste verfügbare Zielländer:"
curl -s "http://localhost:5000/api/flights/destinations" | head -c 200
echo -e "\n"

echo "2. Teste verfügbare Herkunftsländer:"
curl -s "http://localhost:5000/api/flights/origins" | head -c 200
echo -e "\n"

echo "3. Teste Filter nach Deutschland:"
curl -s "http://localhost:5000/api/flights/filter/destination/Germany" | head -c 300
echo -e "\n"

echo "4. Teste Filter von USA:"
curl -s "http://localhost:5000/api/flights/filter/origin/United%20States" | head -c 300
echo -e "\n"

# 2. Test der Route-Service Funktionen
echo "🛫 Teste Flight Routes Service..."

cd /path/to/airtrack_transfer
python3 << 'EOF'
from flight_routes_service import flight_routes_service

# Test Route-Info für bekannte Airlines
test_cases = [
    ("4b1234", "DLH123"),  # Lufthansa
    ("400abc", "BAW456"),  # British Airways  
    ("484def", "AFR789"),  # Air France
    ("44gh12", "UAL321"),  # United Airlines
]

print("🧪 Route-Info Tests:")
for icao24, callsign in test_cases:
    route_info = flight_routes_service.get_flight_route_info(icao24, callsign)
    if route_info:
        print(f"✅ {callsign}: {route_info.airline} - {route_info.origin_country} → {route_info.destination_country}")
    else:
        print(f"❌ {callsign}: Keine Route-Info gefunden")

print("\n📊 Verfügbare Länder-Mappings:")
print(f"Länder: {len(flight_routes_service.country_mapping)}")
for country, variants in list(flight_routes_service.country_mapping.items())[:5]:
    print(f"  {country}: {variants}")

EOF

echo ""
echo "✅ Tests abgeschlossen!"
echo ""
echo "🌐 Öffne http://localhost:5000 zum manuellen Testen:"
echo "   - Filter-Dropdown sollten verfügbar sein"
echo "   - 'Nach Deutschland' Button testen"
echo "   - 'Von USA' Button testen"
echo "   - Flugzeug-Popup sollte Route-Infos zeigen"
echo "   - Status sollte 'In der Luft' oder 'Am Boden' anzeigen"
