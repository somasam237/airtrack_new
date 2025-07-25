#!/usr/bin/env python3
"""
Airtrack Localhost Starter
Startet den Airtrack Web Server auf localhost (127.0.0.1:5000)
"""

import sys
import os
from airtrack_web_server import AirtrackWebServer

def main():
    print(" Starte Airtrack Web Server auf localhost...")
    print("=" * 50)
    
    try:
        # Server auf localhost konfigurieren
        server = AirtrackWebServer(
            host='127.0.0.1',  # Nur localhost
            port=5000,
            debug=True
        )
        
        print(" Server-Konfiguration:")
        print(f"   Host: {server.host}")
        print(f"   Port: {server.port}")
        print(f"   URL: http://{server.host}:{server.port}")
        print()
        print("📍 Öffnen Sie diese URL in Ihrem Browser:")
        print(f"   http://localhost:5000")
        print()
        print("🔧 Zum Stoppen: Ctrl+C drücken")
        print("=" * 50)
        
        # Server starten
        server.run()
        
    except KeyboardInterrupt:
        print("\nServer gestoppt durch Benutzer")
    except Exception as e:
        print(f"\n Fehler beim Starten des Servers: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
