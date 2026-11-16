import json
from urllib.request import urlopen


def lire_mesure(ip, port=8000):
    """Retourne le dictionnaire de mesure d'un capteur, ou None s'il ne répond pas."""
    try:
        with urlopen(f'http://{ip}:{port}/', timeout=1) as reponse:
            return json.load(reponse)
    except Exception:
        return None


if __name__ == '__main__':
    mesure = lire_mesure('127.0.0.1')

    if mesure:
        # À adapter selon les clés exactes renvoyées par le capteur (ex: 'temperature', 'unite', 'unit')
        temp = mesure.get('temperature')
        unite = mesure.get('unite') or mesure.get('unit') or '°C'
        print(f'{temp} {unite}')
    else:
        print('Aucune réponse du capteur.')