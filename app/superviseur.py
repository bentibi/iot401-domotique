"""Le superviseur reçoit les mesures et affiche les alertes."""
import json
import time

from commun import creer_client, HOTE, PORT

TOPICS_CONNUS = {
    'maison/presence-entree/etat',
    'maison/temp-salon/temperature',
    'maison/temp-chambre/temperature',
    'maison/temp-cuisine/temperature',
}
SEUIL_TEMPERATURE = 30.0


def reception(client, donnees, message):
    topic = message.topic

    # Un topic différent des quatre capteurs attendus est signalé.
    if topic not in TOPICS_CONNUS:
        print(f'[ALERTE INTRUSION] Objet inconnu : topic={topic}', flush=True)
        return

    try:
        mesure = json.loads(message.payload.decode('utf-8'))
        valeur = mesure['valeur']

        if topic.endswith('/etat'):
            if not isinstance(valeur, bool):
                raise ValueError('la présence doit être un booléen')
            texte = 'oui' if valeur else 'non'
            print(f'[MESURE] {topic} : {texte}', flush=True)
        else:
            if isinstance(valeur, bool) or not isinstance(valeur, (int, float)):
                raise ValueError('la température doit être numérique')
            print(f'[MESURE] {topic} : {valeur} °C', flush=True)
            if valeur > SEUIL_TEMPERATURE:
                print(f'[ALERTE SEUIL] {topic} : {valeur} °C > {SEUIL_TEMPERATURE} °C', flush=True)
    except (ValueError, KeyError, TypeError, UnicodeDecodeError) as erreur:
        print(f'[ALERTE FORMAT] {topic} : message invalide ({erreur})', flush=True)


def connexion(client, donnees, flags, code, proprietes):
    print(f'[SUPERVISEUR] connexion MQTT : {code}', flush=True)
    if not code.is_failure:
        client.subscribe('maison/#', qos=1)
        print('[SUPERVISEUR] écoute maison/#', flush=True)


def main():
    client = creer_client('superviseur')
    client.on_connect = connexion
    client.on_message = reception
    client.connect_async(HOTE, PORT, keepalive=60)
    client.loop_start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        client.disconnect()
        client.loop_stop()


if __name__ == '__main__':
    main()
