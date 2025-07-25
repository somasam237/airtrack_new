// Globale Variablen
let map;
let socket;
let flightMarkers = {};
let flightPaths = {};
let liveUpdatesEnabled = false;
let currentFilter = null;
let availableDestinations = [];
let availableOrigins = [];

// Initialisierung beim Laden der Seite
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Airtrack JavaScript wird geladen...');
    initializeMap();
    initializeWebSocket();
    initializeFilterControls();
    loadInitialData();
});

/**
 * Karte initialisieren
 */
function initializeMap() {
    try {
        // Karte zentriert auf Europa
        map = L.map('map').setView([50.0, 10.0], 6);
        
        // OpenStreetMap Tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        
        console.log('🗺️ Karte initialisiert');
    } catch (error) {
        console.error('❌ Karte-Initialisierung fehlgeschlagen:', error);
    }
}

/**
 * WebSocket-Verbindung initialisieren
 */
function initializeWebSocket() {
    try {
        socket = io();
        
        socket.on('connect', function() {
            console.log('✅ WebSocket verbunden');
            updateConnectionStatus(true);
        });
        
        socket.on('disconnect', function() {
            console.log('❌ WebSocket getrennt');
            updateConnectionStatus(false);
        });
        
        socket.on('flight_update', function(data) {
            console.log(`✈️ Flight Update: ${data.flights.length} Flugzeuge`);
            updateFlightDisplay(data.flights);
            updateLastUpdate(data.timestamp);
        });
        
        socket.on('status', function(data) {
            console.log('📊 Status:', data.message);
        });
    } catch (error) {
        console.error('❌ WebSocket-Initialisierung fehlgeschlagen:', error);
    }
}

/**
 * Verbindungsstatus in der UI aktualisieren
 */
function updateConnectionStatus(connected) {
    const indicator = document.getElementById('connection-indicator');
    const status = document.getElementById('connection-status');
    
    if (connected) {
        if (indicator) {
            indicator.textContent = '✅ Verbunden';
            indicator.className = 'connection-status connected';
        }
        if (status) {
            status.textContent = 'Verbunden';
        }
    } else {
        if (indicator) {
            indicator.textContent = '❌ Getrennt';
            indicator.className = 'connection-status disconnected';
        }
        if (status) {
            status.textContent = 'Verbindung getrennt';
        }
    }
}

/**
 * Filter-Controls initialisieren
 */
function initializeFilterControls() {
    try {
        // Filter-Buttons Event Listeners
        const btnAllFlights = document.getElementById('btn-all-flights');
        if (btnAllFlights) {
            btnAllFlights.addEventListener('click', () => {
                clearFilter();
                loadFlights();
            });
        }
        
        const btnToGermany = document.getElementById('btn-to-germany');
        if (btnToGermany) {
            btnToGermany.addEventListener('click', () => {
                filterFlightsByDestination('Germany');
            });
        }
        
        const btnFromUSA = document.getElementById('btn-from-usa');
        if (btnFromUSA) {
            btnFromUSA.addEventListener('click', () => {
                filterFlightsByOrigin('United States');
            });
        }
        
        // Dropdown Event Listeners
        const destinationFilter = document.getElementById('destination-filter');
        if (destinationFilter) {
            destinationFilter.addEventListener('change', (e) => {
                if (e.target.value) {
                    filterFlightsByDestination(e.target.value);
                }
            });
        }
        
        const originFilter = document.getElementById('origin-filter');
        if (originFilter) {
            originFilter.addEventListener('change', (e) => {
                if (e.target.value) {
                    filterFlightsByOrigin(e.target.value);
                }
            });
        }
        
        console.log('🎛️ Filter-Controls initialisiert');
    } catch (error) {
        console.error('❌ Filter-Controls Initialisierung fehlgeschlagen:', error);
    }
}

/**
 * Aktuelle Flüge von der API laden
 */
async function loadFlights() {
    try {
        const response = await fetch('/api/flights/current');
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        updateFlightDisplay(data.flights);
        updateFlightsList(data.flights);
        
        console.log(`✈️ ${data.flights.length} aktuelle Flüge geladen`);
    } catch (error) {
        console.error('Fehler beim Laden der Flüge:', error);
        document.getElementById('flights-container').innerHTML = 
            '<div style="color: red;">Fehler beim Laden der Flüge</div>';
    }
}

/**
 * ALLE gespeicherten Flüge aus der Datenbank laden
 */
async function loadAllStoredFlights() {
    try {
        console.log('🗄️ Lade alle gespeicherten Flüge aus der Datenbank...');
        
        const container = document.getElementById('flights-container');
        if (container) {
            container.innerHTML = '<div style="color: blue;">📡 Lade alle gespeicherten Flüge...</div>';
        }
        
        const response = await fetch('/api/flights/database/all');
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Filter-Status aktualisieren
        const filterStatus = document.getElementById('filter-status');
        const flightCount = document.getElementById('flight-count');
        if (filterStatus) filterStatus.textContent = 'Alle gespeicherten Flüge';
        if (flightCount) flightCount.textContent = `(${data.total_count} Flüge)`;
        
        // Flüge anzeigen
        updateFlightDisplay(data.flights);
        updateFlightsList(data.flights);
        
        console.log(`🗄️ ${data.total_count} gespeicherte Flüge aus Datenbank geladen`);
        
    } catch (error) {
        console.error('❌ Fehler beim Laden aller Flüge:', error);
        const container = document.getElementById('flights-container');
        if (container) {
            container.innerHTML = '<div style="color: red;">❌ Fehler beim Laden der gespeicherten Flüge</div>';
        }
    }
}

/**
 * Statistiken von der API laden
 */
async function loadStatistics() {
    try {
        const response = await fetch('/api/statistics');
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        updateStatisticsDisplay(data);
        
    } catch (error) {
        console.error('❌ Fehler beim Laden der Statistiken:', error);
        const container = document.getElementById('stats-container');
        if (container) {
            container.innerHTML = '<div style="color: red;">❌ Fehler beim Laden der Statistiken</div>';
        }
    }
}

/**
 * Flüge auf der Karte anzeigen/aktualisieren
 */
function updateFlightDisplay(flights) {
    if (!map) {
        console.error('❌ Karte nicht initialisiert');
        return;
    }
    
    // Alte Marker entfernen die nicht mehr existieren
    Object.keys(flightMarkers).forEach(icao24 => {
        if (!flights.find(f => f.icao24 === icao24)) {
            map.removeLayer(flightMarkers[icao24]);
            delete flightMarkers[icao24];
        }
    });
    
    // Flüge aktualisieren oder hinzufügen
    flights.forEach(flight => {
        updateFlightMarker(flight);
    });
}

/**
 * Einzelnen Flight Marker aktualisieren oder erstellen
 */
function updateFlightMarker(flight) {
    if (!map) return;
    
    const icao24 = flight.icao24;
    
    // Icon basierend auf Status
    let iconUrl = getFlightIcon(flight);
    
    // Marker erstellen oder aktualisieren
    if (flightMarkers[icao24]) {
        // Bestehenden Marker aktualisieren
        flightMarkers[icao24].setLatLng([flight.latitude, flight.longitude]);
    } else {
        // Neuen Marker erstellen
        const icon = L.icon({
            iconUrl: iconUrl,
            iconSize: [24, 24],
            iconAnchor: [12, 12],
            popupAnchor: [0, -12]
        });
        
        const marker = L.marker([flight.latitude, flight.longitude], { icon: icon })
            .bindPopup(createFlightPopup(flight))
            .addTo(map);
        
        flightMarkers[icao24] = marker;
    }
}

/**
 * Flight Icon basierend auf Status zurückgeben
 */
function getFlightIcon(flight) {
    // Super robuste Lösung mit Canvas
    const canvas = document.createElement('canvas');
    canvas.width = 24;
    canvas.height = 24;
    const ctx = canvas.getContext('2d');
    
    if (flight.on_ground) {
        // Grauer Kreis für am Boden
        ctx.fillStyle = '#666666';
        ctx.beginPath();
        ctx.arc(12, 12, 10, 0, 2 * Math.PI);
        ctx.fill();
        
        // Text "G" für Ground
        ctx.fillStyle = 'white';
        ctx.font = 'bold 12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('G', 12, 16);
    } else {
        // Blauer Kreis für in der Luft
        ctx.fillStyle = '#2196F3';
        ctx.beginPath();
        ctx.arc(12, 12, 10, 0, 2 * Math.PI);
        ctx.fill();
        
        // Text "F" für Flight
        ctx.fillStyle = 'white';
        ctx.font = 'bold 12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('F', 12, 16);
    }
    
    return canvas.toDataURL();
}

/**
 * Flight Popup HTML erstellen
 */
function createFlightPopup(flight) {
    const aircraftInfo = flight.aircraft_info || {};
    const routeInfo = flight.route_info || {};
    
    const statusText = flight.on_ground ? 'Am Boden' : 'In der Luft';
    const statusClass = flight.on_ground ? 'ground' : 'airborne';
    
    let popupContent = `
        <div class="flight-popup">
            <div class="popup-header">
                ✈️ ${flight.callsign}
                <span class="flight-status flight-status-${statusClass}">${statusText}</span>
            </div>
            
            <div class="popup-section">
                <h4>📍 Flugdaten</h4>
                <div class="popup-detail">
                    <span class="popup-label">ICAO24:</span> ${flight.icao24}
                </div>
                <div class="popup-detail">
                    <span class="popup-label">Herkunft:</span> ${flight.origin_country}
                </div>
                <div class="popup-detail">
                    <span class="popup-label">Höhe:</span> ${flight.altitude ? Math.round(flight.altitude) + 'm' : 'N/A'}
                </div>
                <div class="popup-detail">
                    <span class="popup-label">Geschwindigkeit:</span> ${flight.velocity ? Math.round(flight.velocity * 3.6) + ' km/h' : 'N/A'}
                </div>
            </div>
        </div>`;
    
    return popupContent;
}

/**
 * Statistiken-Display aktualisieren
 */
function updateStatisticsDisplay(data) {
    const container = document.getElementById('stats-container');
    if (!container) return;
    
    const flightStats = data.flight_stats || {};
    
    container.innerHTML = `
        <div class="stat-item">
            <span class="stat-label">Aktive Flüge:</span>
            <span class="stat-value">${flightStats.active_flights || 0}</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Gesamte Flüge:</span>
            <span class="stat-value">${flightStats.total_flights || 0}</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Live-Updates:</span>
            <span class="stat-value">${data.live_updates_enabled ? 'Ein' : 'Aus'}</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Interval:</span>
            <span class="stat-value">${data.update_interval}s</span>
        </div>
    `;
}

/**
 * Flight-Liste aktualisieren - ALLE Flüge anzeigen
 */
function updateFlightsList(flights) {
    const container = document.getElementById('flights-container');
    if (!container) return;
    
    if (flights.length === 0) {
        container.innerHTML = '<div class="no-flights">Keine Flüge gefunden</div>';
        return;
    }
    
    // Sortiere Flüge nach Callsign
    const sortedFlights = flights.sort((a, b) => {
        return (a.callsign || 'UNKNOWN').localeCompare(b.callsign || 'UNKNOWN');
    });
    
    let html = `
        <div class="flights-header">
            <h3>✈️ Alle Flüge (${flights.length})</h3>
            <div class="flights-stats">
                🟢 ${flights.filter(f => !f.on_ground).length} in der Luft | 
                🔴 ${flights.filter(f => f.on_ground).length} am Boden
            </div>
        </div>
        <div class="flights-list">
    `;
    
    // ALLE Flüge anzeigen (keine Begrenzung mehr)
    sortedFlights.forEach((flight, index) => {
        const statusClass = flight.on_ground ? 'ground' : 'airborne';
        const statusText = flight.on_ground ? '🔴 Boden' : '🟢 Luft';
        const statusIcon = flight.on_ground ? '🛬' : '✈️';
        
        // Verbesserte Anzeige mit mehr Informationen
        const altitude = flight.altitude ? `${Math.round(flight.altitude)}m` : 'N/A';
        const velocity = flight.velocity ? `${Math.round(flight.velocity * 3.6)} km/h` : 'N/A';
        const country = flight.origin_country || 'Unbekannt';
        
        // Routeninformationen falls verfügbar
        let routeInfo = '';
        if (flight.route_info) {
            const origin = flight.route_info.origin_city || 'N/A';
            const destination = flight.route_info.destination_city || 'N/A';
            const airline = flight.route_info.airline || '';
            routeInfo = `
                <div class="flight-route">
                    <small>${airline} • ${origin} → ${destination}</small>
                </div>
            `;
        }
        
        html += `
            <div class="flight-item ${statusClass}" onclick="focusOnFlight('${flight.icao24}')" title="Auf Karte anzeigen">
                <div class="flight-header">
                    <div class="flight-callsign">
                        ${statusIcon} <strong>${flight.callsign || 'UNKNOWN'}</strong>
                    </div>
                    <div class="flight-status flight-status-${statusClass}">
                        ${statusText}
                    </div>
                </div>
                
                <div class="flight-details">
                    <div class="flight-country">
                        🌍 <strong>${country}</strong>
                    </div>
                    <div class="flight-icao">
                        📡 ${flight.icao24}
                    </div>
                </div>
                
                <div class="flight-data">
                    <div class="flight-metric">
                        <span class="metric-label">Höhe:</span>
                        <span class="metric-value">${altitude}</span>
                    </div>
                    <div class="flight-metric">
                        <span class="metric-label">Speed:</span>
                        <span class="metric-value">${velocity}</span>
                    </div>
                </div>
                
                ${routeInfo}
                
                <div class="flight-coordinates">
                    <small>📍 ${flight.latitude.toFixed(3)}, ${flight.longitude.toFixed(3)}</small>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    
    container.innerHTML = html;
    
    // Scroll-to-top Button hinzufügen
    if (flights.length > 10) {
        html += `
            <div class="scroll-controls">
                <button onclick="scrollToTop()" class="btn btn-small">
                    ⬆️ Nach oben
                </button>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

/**
 * Auf spezifischen Flug fokussieren
 */
function focusOnFlight(icao24) {
    const marker = flightMarkers[icao24];
    if (marker && map) {
        map.setView(marker.getLatLng(), 10);
        marker.openPopup();
    }
}

/**
 * Verfügbare Zielländer laden
 */
async function loadAvailableDestinations() {
    try {
        const response = await fetch('/api/flights/destinations');
        const data = await response.json();
        
        if (data.error) {
            console.error('❌ Fehler beim Laden der Ziele:', data.error);
            return;
        }
        
        availableDestinations = data.destinations || [];
        updateDestinationFilter();
        
    } catch (error) {
        console.error('❌ Fehler beim Laden der verfügbaren Ziele:', error);
    }
}

/**
 * Verfügbare Herkunftsländer laden
 */
async function loadAvailableOrigins() {
    try {
        const response = await fetch('/api/flights/origins');
        const data = await response.json();
        
        if (data.error) {
            console.error('❌ Fehler beim Laden der Herkunftsländer:', data.error);
            return;
        }
        
        availableOrigins = data.origins || [];
        updateOriginFilter();
        
    } catch (error) {
        console.error('❌ Fehler beim Laden der verfügbaren Herkunftsländer:', error);
    }
}

/**
 * Destination Filter-Dropdown aktualisieren
 */
function updateDestinationFilter() {
    const select = document.getElementById('destination-filter');
    if (!select) return;
    
    while (select.children.length > 1) {
        select.removeChild(select.lastChild);
    }
    
    availableDestinations.forEach(country => {
        const option = document.createElement('option');
        option.value = country;
        option.textContent = country;
        select.appendChild(option);
    });
}

/**
 * Origin Filter-Dropdown aktualisieren
 */
function updateOriginFilter() {
    const select = document.getElementById('origin-filter');
    if (!select) return;
    
    while (select.children.length > 1) {
        select.removeChild(select.lastChild);
    }
    
    availableOrigins.forEach(country => {
        const option = document.createElement('option');
        option.value = country;
        option.textContent = country;
        select.appendChild(option);
    });
}

/**
 * Nach Zielland filtern
 */
async function filterFlightsByDestination(country) {
    try {
        console.log(`🎯 Filtere Flüge nach Zielland: ${country}`);
        
        const response = await fetch(`/api/flights/filter/destination/${encodeURIComponent(country)}`);
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        const filterStatus = document.getElementById('filter-status');
        const flightCount = document.getElementById('flight-count');
        if (filterStatus) filterStatus.textContent = `Nach ${country}`;
        if (flightCount) flightCount.textContent = `(${data.total_count} Flüge)`;
        
        updateFlightDisplay(data.flights);
        updateFlightsList(data.flights);
        
        console.log(`✅ ${data.total_count} Flüge nach ${country} gefiltert`);
        
    } catch (error) {
        console.error('❌ Fehler beim Filtern nach Zielland:', error);
    }
}

/**
 * Nach Herkunftsland filtern
 */
async function filterFlightsByOrigin(country) {
    try {
        console.log(`🛫 Filtere Flüge von Herkunftsland: ${country}`);
        
        const response = await fetch(`/api/flights/filter/origin/${encodeURIComponent(country)}`);
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        const filterStatus = document.getElementById('filter-status');
        const flightCount = document.getElementById('flight-count');
        if (filterStatus) filterStatus.textContent = `Von ${country}`;
        if (flightCount) flightCount.textContent = `(${data.total_count} Flüge)`;
        
        updateFlightDisplay(data.flights);
        updateFlightsList(data.flights);
        
        console.log(`✅ ${data.total_count} Flüge von ${country} gefiltert`);
        
    } catch (error) {
        console.error('❌ Fehler beim Filtern nach Herkunftsland:', error);
    }
}

/**
 * Filter zurücksetzen
 */
function clearFilter() {
    const filterStatus = document.getElementById('filter-status');
    const flightCount = document.getElementById('flight-count');
    const destinationFilter = document.getElementById('destination-filter');
    const originFilter = document.getElementById('origin-filter');
    
    if (filterStatus) filterStatus.textContent = 'Alle Flüge';
    if (flightCount) flightCount.textContent = '';
    if (destinationFilter) destinationFilter.value = '';
    if (originFilter) originFilter.value = '';
    
    console.log('🧹 Filter zurückgesetzt');
}

/**
 * Live-Updates umschalten
 */
async function toggleLiveUpdates() {
    try {
        console.log('🔄 Toggle Live-Updates...');
        
        const response = await fetch('/api/control/live-updates', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                enable: !liveUpdatesEnabled
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        liveUpdatesEnabled = data.live_updates_enabled;
        updateLiveUpdateButton();
        
        console.log(`✅ Live-Updates: ${liveUpdatesEnabled ? 'aktiviert' : 'deaktiviert'}`);
        
        // Status-Nachricht anzeigen
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            const originalText = statusElement.textContent;
            statusElement.textContent = `${liveUpdatesEnabled ? '🟢' : '🔴'} Live-Updates ${liveUpdatesEnabled ? 'gestartet' : 'gestoppt'}`;
            statusElement.style.color = liveUpdatesEnabled ? 'green' : 'orange';
            
            setTimeout(() => {
                statusElement.textContent = originalText;
                statusElement.style.color = '';
            }, 3000);
        }
        
    } catch (error) {
        console.error('❌ Fehler beim Umschalten der Live-Updates:', error);
        
        // Fehler-Nachricht anzeigen
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            const originalText = statusElement.textContent;
            statusElement.textContent = '❌ Live-Update Fehler';
            statusElement.style.color = 'red';
            
            setTimeout(() => {
                statusElement.textContent = originalText;
                statusElement.style.color = '';
            }, 3000);
        }
    }
}

/**
 * Live-Update Button aktualisieren
 */
function updateLiveUpdateButton() {
    const button = document.getElementById('live-updates-btn');
    if (button) {
        if (liveUpdatesEnabled) {
            button.textContent = 'Live-Updates stoppen';
            button.className = 'btn btn-danger';
        } else {
            button.textContent = 'Live-Updates starten';
            button.className = 'btn btn-success';
        }
    }
}

/**
 * Daten manuell aktualisieren
 */
async function refreshData() {
    console.log('🔄 Aktualisiere Daten manuell...');
    try {
        await Promise.all([
            loadFlights(),
            loadStatistics()
        ]);
        console.log('✅ Daten erfolgreich aktualisiert');
    } catch (error) {
        console.error('❌ Fehler beim Aktualisieren der Daten:', error);
    }
}

/**
 * Karte zentrieren
 */
function centerMap() {
    if (map) {
        map.setView([50.0, 10.0], 6);
        console.log('🎯 Karte zentriert');
    } else {
        console.error('❌ Karte nicht verfügbar');
    }
}

/**
 * Letztes Update-Time anzeigen
 */
function updateLastUpdate(timestamp) {
    const time = new Date(timestamp).toLocaleTimeString();
    console.log(`⏰ Letztes Update: ${time}`);
}

/**
 * Nach oben scrollen
 */
function scrollToTop() {
    const container = document.getElementById('flights-container');
    if (container) {
        container.scrollTop = 0;
    }
    window.scrollTo(0, 0);
}

/**
 * Test-Funktion: Fügt einige Test-Flugzeuge zur Karte hinzu
 */
function addTestFlights() {
    console.log('🧪 Füge Test-Flugzeuge hinzu...');
    
    const testFlights = [
        {
            icao24: 'test001',
            callsign: 'LH441',
            origin_country: 'Germany',
            latitude: 52.5,
            longitude: 13.4, // Berlin
            altitude: 10000,
            velocity: 250,
            true_track: 90,
            on_ground: false,
            route_info: {
                origin_city: 'Berlin',
                destination_city: 'Munich',
                airline: 'Lufthansa'
            }
        },
        {
            icao24: 'test002',
            callsign: 'AF1234',
            origin_country: 'France',
            latitude: 48.8,
            longitude: 2.3, // Paris
            altitude: 0,
            velocity: 0,
            true_track: 0,
            on_ground: true,
            route_info: {
                origin_city: 'Paris',
                destination_city: 'London',
                airline: 'Air France'
            }
        },
        {
            icao24: 'test003',
            callsign: 'BA987',
            origin_country: 'United Kingdom',
            latitude: 51.5,
            longitude: -0.1, // London
            altitude: 8500,
            velocity: 180,
            true_track: 45,
            on_ground: false,
            route_info: {
                origin_city: 'London',
                destination_city: 'Frankfurt',
                airline: 'British Airways'
            }
        }
    ];
    
    // Test-Flüge zur Karte hinzufügen
    updateFlightDisplay(testFlights);
    updateFlightsList(testFlights);
    
    // Filter-Status aktualisieren
    const filterStatus = document.getElementById('filter-status');
    const flightCount = document.getElementById('flight-count');
    if (filterStatus) filterStatus.textContent = 'Test-Flüge';
    if (flightCount) flightCount.textContent = `(${testFlights.length} Flüge)`;
    
    console.log(`✅ ${testFlights.length} Test-Flugzeuge hinzugefügt`);
}

// Test-Funktion global verfügbar machen
window.addTestFlights = addTestFlights;
