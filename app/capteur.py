"""Simulateur d'un des quatre capteurs de la maison."""
import json
import os
import random
import time
from commun import creer_client, HOTE, PORT

IDENTITE = os.environ['CAPTEUR_ID']
TOPICS = {
    'presence-entree': 'maison/presence-entree/etat',
    'temp-salon': 'maison/temp-salon/temperature',
    'temp-chambre': 'maison/temp-chambre/temperature',
    'temp-cuisine': 'maison/temp-cuisine/temperature',
}
if IDENTITE not in TOPICS:
    raise SystemExit('Identité de capteur non reconnue')

TOPIC = TOPICS[IDENTITE]
INTERVALLE = 8 if IDENTITE == 'presence-entree' else 10


def nouvelle_valeur():
    if IDENTITE == 'presence-entree':
        return random.random() < 0.25  # Oui/non, aucun nom ni image.
    bornes = {
        'temp-salon': (20, 24),
        'temp-chambre': (18, 22),
        'temp-cuisine': (21, 27),
    }
    return round(random.uniform(*bornes[IDENTITE]), 1)


def main():
    client = creer_client(IDENTITE)
    client.on_connect = lambda c, u, flags, rc, p: print(f'[{IDENTITE}] connexion MQTT : {rc}')
    client.connect_async(HOTE, PORT, keepalive=60)
    client.loop_start()
    try:
        while True:
            if client.is_connected():
                valeur = nouvelle_valeur()
                donnees = json.dumps({'valeur': valeur}, separators=(',', ':'))
                resultat = client.publish(TOPIC, donnees, qos=1, retain=False)
                if resultat.rc == 0:
                    print(f'[{IDENTITE}] {TOPIC} -> {donnees}')
                else:
                    print(f'[{IDENTITE}] erreur publication : {resultat.rc}')
            else:
                print(f'[{IDENTITE}] attente du broker...')
            time.sleep(INTERVALLE)
    except KeyboardInterrupt:
        pass
    finally:
        client.disconnect()
        client.loop_stop()


if __name__ == '__main__':
    main()
