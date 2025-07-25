-- Airtrack Database Schema für Ubuntu VM



-- Mit Database verbinden
\c airtrack_db;

-- Aircraft Tabelle
CREATE TABLE IF NOT EXISTS aircraft (
    icao24 VARCHAR(10) PRIMARY KEY,
    registration VARCHAR(20),
    aircraft_type VARCHAR(100),
    manufacturer VARCHAR(50),
    model VARCHAR(50),
    airline VARCHAR(100),
    airline_iata VARCHAR(3),
    airline_icao VARCHAR(4),
    owner VARCHAR(100),
    operator VARCHAR(100),
    construction_number VARCHAR(20),
    first_flight DATE,
    engines VARCHAR(50),
    seats INTEGER,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Flights Tabelle
CREATE TABLE IF NOT EXISTS flights (
    flight_id SERIAL PRIMARY KEY,
    icao24 VARCHAR(10) NOT NULL REFERENCES aircraft(icao24),
    callsign VARCHAR(20),
    origin_country VARCHAR(100),
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    flight_status VARCHAR(20) DEFAULT 'unknown',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Flight Positions Tabelle
CREATE TABLE IF NOT EXISTS flight_positions (
    position_id SERIAL PRIMARY KEY,
    flight_id INTEGER NOT NULL REFERENCES flights(flight_id),
    icao24 VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    latitude DECIMAL(10, 6),
    longitude DECIMAL(11, 6),
    altitude DECIMAL(10, 2),
    velocity DECIMAL(8, 2),
    true_track DECIMAL(6, 2),
    vertical_rate DECIMAL(8, 2),
    on_ground BOOLEAN DEFAULT FALSE,
    squawk VARCHAR(4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Flight Statistics Tabelle
CREATE TABLE IF NOT EXISTS flight_statistics (
    stat_id SERIAL PRIMARY KEY,
    date DATE DEFAULT CURRENT_DATE,
    total_flights INTEGER DEFAULT 0,
    active_flights INTEGER DEFAULT 0,
    total_positions INTEGER DEFAULT 0,
    unique_aircraft INTEGER DEFAULT 0,
    database_writes INTEGER DEFAULT 0,
    database_errors INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data Updates Tabelle (für Monitoring)
CREATE TABLE IF NOT EXISTS data_updates (
    update_id SERIAL PRIMARY KEY,
    update_type VARCHAR(50),
    total_aircraft INTEGER,
    processed_aircraft INTEGER,
    new_flights INTEGER,
    positions_added INTEGER,
    errors INTEGER DEFAULT 0,
    processing_time DECIMAL(6, 3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_aircraft_icao24 ON aircraft(icao24);
CREATE INDEX IF NOT EXISTS idx_flights_icao24 ON flights(icao24);
CREATE INDEX IF NOT EXISTS idx_flights_status ON flights(flight_status);
CREATE INDEX IF NOT EXISTS idx_flights_last_seen ON flights(last_seen);
CREATE INDEX IF NOT EXISTS idx_positions_flight_id ON flight_positions(flight_id);
CREATE INDEX IF NOT EXISTS idx_positions_icao24 ON flight_positions(icao24);
CREATE INDEX IF NOT EXISTS idx_positions_timestamp ON flight_positions(timestamp);
CREATE INDEX IF NOT EXISTS idx_positions_lat_lng ON flight_positions(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_statistics_date ON flight_statistics(date);
CREATE INDEX IF NOT EXISTS idx_updates_created ON data_updates(created_at);

-- Trigger für updated_at Automatisierung
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger anwenden
CREATE TRIGGER update_aircraft_updated_at BEFORE UPDATE ON aircraft
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_flights_updated_at BEFORE UPDATE ON flights
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_statistics_updated_at BEFORE UPDATE ON flight_statistics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views für einfache Abfragen
CREATE OR REPLACE VIEW active_flights_view AS
SELECT 
    f.flight_id,
    f.icao24,
    f.callsign,
    f.origin_country,
    f.flight_status,
    f.last_seen,
    a.aircraft_type,
    a.airline,
    COUNT(fp.position_id) as position_count,
    MAX(fp.timestamp) as latest_position
FROM flights f
LEFT JOIN aircraft a ON f.icao24 = a.icao24
LEFT JOIN flight_positions fp ON f.flight_id = fp.flight_id
WHERE f.last_seen >= NOW() - INTERVAL '2 hours'
GROUP BY f.flight_id, f.icao24, f.callsign, f.origin_country, 
         f.flight_status, f.last_seen, a.aircraft_type, a.airline
ORDER BY f.last_seen DESC;

CREATE OR REPLACE VIEW flight_statistics_view AS
SELECT 
    date,
    total_flights,
    active_flights,
    total_positions,
    unique_aircraft,
    database_writes,
    database_errors,
    CASE 
        WHEN database_writes > 0 
        THEN ROUND((database_errors::DECIMAL / database_writes) * 100, 2)
        ELSE 0 
    END as error_rate_percent
FROM flight_statistics
ORDER BY date DESC;

-- Beispiel-Aircraft für Tests einfügen
INSERT INTO aircraft (icao24, registration, aircraft_type, manufacturer, model, airline, airline_iata, airline_icao, category)
VALUES 
    ('4b1814', 'HB-JNA', 'Airbus A320-214', 'Airbus', 'A320-214', 'Swiss International Air Lines', 'LX', 'SWR', 'Commercial'),
    ('3c6444', 'D-AIQD', 'Airbus A320-211', 'Airbus', 'A320-211', 'Lufthansa', 'LH', 'DLH', 'Commercial'),
    ('a12345', 'N123AB', 'Boeing 737-800', 'Boeing', '737-800', 'American Airlines', 'AA', 'AAL', 'Commercial'),
    ('a98765', 'N987XY', 'Cessna 172', 'Cessna', '172', NULL, NULL, NULL, 'General Aviation')
ON CONFLICT (icao24) DO NOTHING;

-- Berechtigung für airtrack_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO airtrack_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO airtrack_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO airtrack_user;

-- Schema-Information anzeigen
\dt
\di

SELECT 'Airtrack Database Schema erfolgreich erstellt!' as status;
