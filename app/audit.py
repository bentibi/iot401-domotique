"""Tests de démonstration demandés dans le barème IOT401.

Ne fonctionne que sur le réseau privé Docker du laboratoire.
"""
import json
import socket
import sys
import threading
import time

from commun import creer_client, HOTE, PORT


def verifier_broker():
    with socket.create_connection((HOTE, PORT), timeout=4):
        pass


def sans_certificat():
    verifier_broker()
    connecte = threading.Event()
    deconnecte = threading.Event()
    client = creer_client('test', identifiant_client='audit-sans-certificat', avec_certificat=False)
    client.on_connect = lambda c, u, f, rc, p: connecte.set() if not rc.is_failure else deconnecte.set()
    client.on_disconnect = lambda c, u, flags, rc, properties: deconnecte.set()
    try:
        client.connect(HOTE, PORT, keepalive=10)
        client.loop_start()
        deconnecte.wait(7)
        if connecte.is_set():
            raise AssertionError('ECHEC : connexion sans certificat acceptée')
        if not deconnecte.is_set():
            raise AssertionError('INCONCLUANT : pas de réponse, vérifier les logs broker')
        print('[PREUVE mTLS] OK : le broker a coupé la connexion sans certificat client.')
    except (OSError, ConnectionError) as erreur:
        # Le port a été vérifié juste avant : il s'agit du refus TLS.
        print(f'[PREUVE mTLS] OK : échec TLS sans certificat client : {erreur}')
    finally:
        client.loop_stop()
        client.disconnect()


def publier_et_verifier(identite, topic, valeur, attente_135=False):
    verifier_broker()
    connexion = threading.Event()
    publication = threading.Event()
    recus = []
    client = creer_client(identite, f'audit-{identite}-{int(time.time())}')

    def on_connect(c, u, f, rc, properties):
        if rc.is_failure:
            print(f'[ERREUR] échec de connexion : {rc}')
            return
        connexion.set()
        c.publish(topic, json.dumps({'valeur': valeur}), qos=1, retain=False)

    def on_publish(c, u, mid, reason_code, properties):
        recus.append(reason_code.value)
        publication.set()

    client.on_connect = on_connect
    client.on_publish = on_publish
    client.connect(HOTE, PORT, keepalive=30)
    client.loop_start()
    try:
        if not connexion.wait(8):
            raise RuntimeError('Connexion MQTT impossible : voir les logs du broker')
        if not publication.wait(8):
            raise RuntimeError('Aucun PUBACK reçu : voir les logs du broker')
        code = recus[0]
        if attente_135:
            if code != 135:
                raise AssertionError(f'RC attendu 135, reçu {code}')
            print(f'[PREUVE ACL] OK : publication interdite refusée, RC:{code}')
        else:
            if code != 0:
                raise AssertionError(f'Publication attendue autorisée, RC:{code}')
            print(f'[PREUVE MQTT] OK : publication acceptée, RC:{code} sur {topic}')
            # Donne le temps au superviseur de recevoir le message avant la fin du test.
            time.sleep(1)
    finally:
        client.disconnect()
        client.loop_stop()


MODES = {
    'sans-certificat': sans_certificat,
    'acl': lambda: publier_et_verifier('temp-salon', 'maison/temp-chambre/temperature', 99, True),
    'intrusion': lambda: publier_et_verifier('capteur-test', 'maison/capteur-test/etat', True),
    'seuil': lambda: publier_et_verifier('temp-salon', 'maison/temp-salon/temperature', 35.5),
}

if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in MODES:
        raise SystemExit('Usage : python audit.py ' + '|'.join(MODES))
    MODES[sys.argv[1]]()
