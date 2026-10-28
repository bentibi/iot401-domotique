"""Envoi de fausses mesures de température ou de présence."""
import json
import os
import random
import time

from commun import creer_client, HOTE, PORT

# Une seule application Python sert aux quatre conteneurs.
IDENTITE = os.environ['CAPTEUR_ID']
TOPICS = {
    'presence-entree': 'maison/presence-entree/etat',
    'temp-salon': 'maison/temp-salon/temperature',
    'temp-chambre': 'maison/temp-chambre/temperature',
    'temp-cuisine': 'maison/temp-cuisine/temperature',
}
if IDENTITE not in TOPICS:
    raise SystemExit('Capteur inconnu : ' + IDENTITE)

TOPIC = TOPICS[IDENTITE]
INTERVALLE = 8 if IDENTITE == 'presence-entree' else 10


def nouvelle_valeur():
    if IDENTITE == 'presence-entree':
        # On simule seulement oui/non, sans image ni nom.
        return random.random() < 0.25

    temperatures = {
        'temp-salon': (20, 24),
        'temp-chambre': (18, 22),
        'temp-cuisine': (21, 27),
    }
    minimum, maximum = temperatures[IDENTITE]
    return round(random.uniform(minimum, maximum), 1)


def connexion(client, donnees, flags, code, proprietes):
    print(f'[{IDENTITE}] connexion MQTT : {code}')


def main():
    client = creer_client(IDENTITE)
    client.on_connect = connexion
    client.connect_async(HOTE, PORT, keepalive=60)
    client.loop_start()

    try:
        while True:
            if client.is_connected():
                mesure = json.dumps({'valeur': nouvelle_valeur()})
                resultat = client.publish(TOPIC, mesure, qos=1, retain=False)
                if resultat.rc == 0:
                    print(f'[{IDENTITE}] {TOPIC} -> {mesure}')
                else:
                    print(f'[{IDENTITE}] erreur de publication : {resultat.rc}')
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
