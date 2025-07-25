#!/bin/bash
# SSH Tunnel Setup für Airtrack VM Access
# Dieses Script erstellt einen SSH-Tunnel zur Ubuntu VM

echo "🔗 SSH Tunnel Setup für Airtrack"
echo "=================================="

# VM Verbindungsdaten (anpassen!)
VM_USER="your-username"          
VM_HOST="your-vm-ip"             
VM_PORT="22"                     # SSH Port (meist 22)
LOCAL_PORT="5000"               
REMOTE_PORT="5000"               
echo "📋 Konfiguration:"
echo "   VM Benutzer: $VM_USER"
echo "   VM Host: $VM_HOST"
echo "   SSH Port: $VM_PORT"
echo "   Local Port: $LOCAL_PORT"
echo "   Remote Port: $REMOTE_PORT"
echo ""

# SSH Tunnel erstellen
echo " Erstelle SSH Tunnel..."
echo "   Kommando: ssh -L $LOCAL_PORT:localhost:$REMOTE_PORT -N $VM_USER@$VM_HOST"
echo ""
echo " Nach dem Start können Sie zugreifen auf:"
echo "   http://localhost:$LOCAL_PORT"
echo ""
echo " Zum Beenden: Ctrl+C"
echo ""

# SSH Tunnel starten
ssh -L $LOCAL_PORT:localhost:$REMOTE_PORT -N $VM_USER@$VM_HOST
