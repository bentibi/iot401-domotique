"""Supervision locale. Aucun stockage permanent des mesures."""
import json
import time
from commun import creer_client, HOTE, PORT

SUJETS_AUTORISES = {
    'maison/presence-entree/etat',
    'maison/temp-salon/temperature',
    'maison/temp-chambre/temperature',
    'maison/temp-cuisine/temperature',
}
SEUIL_TEMPERATURE = 30.0


def reception(client, userdata, message):
    topic = message.topic
    if topic not in SUJETS_AUTORISES:
        print(f'[ALERTE INTRUSION] Objet inconnu : topic={topic}', flush=True)
        return
    try:
        donnees = json.loads(message.payload.decode('utf-8'))
        valeur = donnees['valeur']
        if topic.endswith('/etat'):
            if not isinstance(valeur, bool):
                raise ValueError('la présence doit être un booléen')
            print(f'[MESURE] {topic} : {"oui" if valeur else "non"}', flush=True)
        else:
            if isinstance(valeur, bool) or not isinstance(valeur, (int, float)):
                raise ValueError('la température doit être numérique')
            print(f'[MESURE] {topic} : {valeur} °C', flush=True)
            if valeur > SEUIL_TEMPERATURE:
                print(f'[ALERTE SEUIL] {topic} : {valeur} °C > {SEUIL_TEMPERATURE} °C', flush=True)
    except (ValueError, KeyError, TypeError, UnicodeDecodeError) as erreur:
        print(f'[ALERTE FORMAT] {topic} : message invalide ({erreur})', flush=True)


def main():
    client = creer_client('superviseur')
    def connexion(c, u, flags, rc, properties):
        print(f'[SUPERVISEUR] connexion MQTT : {rc}', flush=True)
        if not rc.is_failure:
            c.subscribe('maison/#', qos=1)
            print('[SUPERVISEUR] écoute maison/#', flush=True)
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
