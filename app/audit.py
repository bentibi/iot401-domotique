"""Quatre tests de sécurité lancés dans le réseau Docker du projet."""
import json
import socket
import sys
import threading
import time

from commun import creer_client, HOTE, PORT


def verifier_broker():
    # Le broker doit déjà répondre avant d'essayer un test.
    with socket.create_connection((HOTE, PORT), timeout=4):
        pass


def sans_certificat():
    verifier_broker()
    connexion = threading.Event()
    deconnexion = threading.Event()
    client = creer_client('test', 'audit-sans-certificat', avec_certificat=False)

    def on_connect(c, donnees, flags, code, proprietes):
        if code.is_failure:
            deconnexion.set()
        else:
            connexion.set()

    def on_disconnect(c, donnees, flags, code, proprietes):
        deconnexion.set()

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    try:
        client.connect(HOTE, PORT, keepalive=10)
        client.loop_start()
        deconnexion.wait(7)

        if connexion.is_set():
            raise AssertionError('ECHEC : le broker a accepté un client sans certificat')
        if not deconnexion.is_set():
            raise AssertionError('INCONCLUANT : vérifier les logs du broker')
        print('[PREUVE mTLS] OK : le broker a coupé la connexion sans certificat client.')
    except OSError as erreur:
        print(f'[PREUVE mTLS] OK : échec TLS sans certificat client : {erreur}')
    finally:
        client.loop_stop()
        client.disconnect()


def publier_et_verifier(identite, topic, valeur, refus_attendu=False):
    verifier_broker()
    connexion = threading.Event()
    publication = threading.Event()
    codes = []
    client = creer_client(identite, f'audit-{identite}-{int(time.time())}')

    def on_connect(c, donnees, flags, code, proprietes):
        if not code.is_failure:
            connexion.set()
            c.publish(topic, json.dumps({'valeur': valeur}), qos=1, retain=False)

    def on_publish(c, donnees, message_id, code, proprietes):
        codes.append(code.value)
        publication.set()

    client.on_connect = on_connect
    client.on_publish = on_publish
    client.connect(HOTE, PORT, keepalive=30)
    client.loop_start()
    try:
        if not connexion.wait(8):
            raise RuntimeError('Connexion MQTT impossible : voir les logs du broker')
        if not publication.wait(8):
            raise RuntimeError('Aucun PUBACK reçu')

        code = codes[0]
        if refus_attendu:
            if code != 135:
                raise AssertionError(f'RC attendu : 135, RC reçu : {code}')
            print('[PREUVE ACL] OK : publication interdite refusée, RC:135')
        else:
            if code != 0:
                raise AssertionError(f'Publication refusée, RC:{code}')
            print(f'[PREUVE MQTT] OK : publication acceptée, RC:0 sur {topic}')
            time.sleep(1)
    finally:
        client.disconnect()
        client.loop_stop()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage : python audit.py [sans-certificat|acl|intrusion|seuil]')
    test = sys.argv[1]
    if test == 'sans-certificat':
        sans_certificat()
    elif test == 'acl':
        publier_et_verifier('temp-salon', 'maison/temp-chambre/temperature', 99, True)
    elif test == 'intrusion':
        publier_et_verifier('capteur-test', 'maison/capteur-test/etat', True)
    elif test == 'seuil':
        publier_et_verifier('temp-salon', 'maison/temp-salon/temperature', 35.5)
    else:
        raise SystemExit('Test inconnu : ' + test)
