"""Fonctions MQTT communes aux capteurs et au superviseur."""
import ssl
from pathlib import Path
import paho.mqtt.client as mqtt

HOTE = 'broker'
PORT = 8883


def creer_client(identite, identifiant_client=None, avec_certificat=True):
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=identifiant_client or identite,
        protocol=mqtt.MQTTv5,
    )
    dossier = Path('/certs')
    contexte = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=str(dossier / 'ca.crt'))
    contexte.minimum_version = ssl.TLSVersion.TLSv1_2
    contexte.check_hostname = True  # Le serveur doit s'appeler « broker ».
    contexte.verify_mode = ssl.CERT_REQUIRED
    if avec_certificat:
        contexte.load_cert_chain(str(dossier / 'client.crt'), str(dossier / 'client.key'))
    client.tls_set_context(contexte)
    # Pas de tls_insecure_set(True) : la validation du serveur est obligatoire.
    return client
