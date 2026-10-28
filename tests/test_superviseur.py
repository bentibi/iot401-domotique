"""Petits tests des règles de supervision, sans démarrer Docker."""
import contextlib
import io
import json
import sys
import types
import unittest
from pathlib import Path

# Pour tester reception(), on n'a pas besoin de se connecter au broker.
# On remplace juste le module MQTT par un module vide.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
sys.modules.setdefault('commun', types.SimpleNamespace(creer_client=None, HOTE='broker', PORT=8883))
from superviseur import reception


def envoyer(topic, valeur):
    message = types.SimpleNamespace(topic=topic, payload=json.dumps({'valeur': valeur}).encode())
    sortie = io.StringIO()
    with contextlib.redirect_stdout(sortie):
        reception(None, None, message)
    return sortie.getvalue()


class TestSuperviseur(unittest.TestCase):
    def test_temperature_normale(self):
        resultat = envoyer('maison/temp-chambre/temperature', 20.4)
        self.assertIn('[MESURE]', resultat)
        self.assertNotIn('[ALERTE SEUIL]', resultat)

    def test_seuil(self):
        resultat = envoyer('maison/temp-salon/temperature', 35.5)
        self.assertIn('[ALERTE SEUIL]', resultat)

    def test_presence(self):
        resultat = envoyer('maison/presence-entree/etat', True)
        self.assertIn(': oui', resultat)

    def test_objet_inconnu(self):
        resultat = envoyer('maison/capteur-test/etat', True)
        self.assertIn('[ALERTE INTRUSION]', resultat)

    def test_format_invalide(self):
        resultat = envoyer('maison/temp-cuisine/temperature', 'chaud')
        self.assertIn('[ALERTE FORMAT]', resultat)


if __name__ == '__main__':
    unittest.main()
