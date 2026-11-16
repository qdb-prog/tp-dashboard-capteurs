"""
Simulateur de capteur météo.
Génère toutes les 20 secondes une mesure aléatoire (température, pression,
humidité) et la publie en JSON via un serveur HTTP.

Lancement :  python capteur.py
"""

import json
import random
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import socket



### Changer le nom du capteur pour lui donner votre nom
NOM_CAPTEUR = "Station-Nom-Prenom"


INTERVALLE_S = 20
HOST, PORT = "0.0.0.0", 8000

# Zone approximative de l'Île-de-France
LAT_MIN, LAT_MAX = 48.60, 49.05
LON_MIN, LON_MAX = 2.00, 2.70

# Tirés une seule fois : le capteur est fixe et cultive une seule plante
POSITION = {
    "latitude": round(random.uniform(LAT_MIN, LAT_MAX), 5),
    "longitude": round(random.uniform(LON_MIN, LON_MAX), 5),
}
PLANTES = ["Tomate", "Laitue", "Fraisier", "Basilic", "Carotte"]
PLANTE = random.choice(PLANTES)
# Dernière mesure partagée entre le thread de mesure et le serveur HTTP
derniere_mesure = {}
verrou = threading.Lock()


def generer_mesure():
    """Crée une mesure aléatoire au format dictionnaire."""
    return {
        "nom": NOM_CAPTEUR,
        "date_heure": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "position": POSITION,
        "plante": PLANTE,
        "temperature": {"valeur": round(random.uniform(-10, 40), 1), "unite": "°C"},
        "pression": {"valeur": round(random.uniform(980, 1040), 1), "unite": "hPa"},
        "humidite": {"valeur": round(random.uniform(20, 100), 1), "unite": "%"},
    }

def boucle_mesures():
    """Thread : met à jour la mesure toutes les INTERVALLE_S secondes."""
    global derniere_mesure
    while True:
        mesure = generer_mesure()
        with verrou:
            derniere_mesure = mesure
        print(f"[{mesure['date_heure']}] Nouvelle mesure générée")
        time.sleep(INTERVALLE_S)

def obtenir_ip_locale():
    """Retourne l'adresse IP de la machine sur le réseau local."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Aucune donnée n'est envoyée : on demande juste quelle interface serait utilisée
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()

def annonce_broadcast():
    """Annonce la présence du capteur sur le réseau toutes les 20 s."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        message = json.dumps({"nom": NOM_CAPTEUR, "port": PORT}).encode()
        s.sendto(message, ("255.255.255.255", 9999))
        time.sleep(INTERVALLE_S)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/mesure"):
            with verrou:
                corps = json.dumps(derniere_mesure, ensure_ascii=False, indent=2)
            donnees = corps.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(donnees)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(donnees)
        else:
            self.send_error(404, "Ressource introuvable")

    def log_message(self, format, *args):
        horodatage = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{horodatage}] Requête de {self.client_address[0]} : {self.path}")

if __name__ == "__main__":
    derniere_mesure = generer_mesure()

    threading.Thread(target=boucle_mesures, daemon=True).start()
    threading.Thread(target=annonce_broadcast, daemon=True).start()


    ip_locale = obtenir_ip_locale()
    serveur = HTTPServer((HOST, PORT), Handler)
    print(f"Serveur démarré (Ctrl+C pour arrêter)")
    print(f"  Local  : http://localhost:{PORT}/")
    print(f"  Réseau : http://{ip_locale}:{PORT}/")
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur.")
        serveur.server_close()