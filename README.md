# IOT401 - Maison connectée sécurisée

Projet de domotique du module IOT401 à l'École 2600.  
**Binôme :** Benjamin TIBI (`bentibi`) et Ilias EL HOUZI (`SaitamaDuBled`)  
**Professeur :** Marouane El Moufid

## Notre objectif

Nous simulons quatre capteurs domestiques. Ils envoient des mesures à un broker Mosquitto avec MQTT v5 et mTLS. Le superviseur lit les données et affiche deux alertes : température supérieure à 30 °C et objet hors de notre liste.

| Capteur | Mesure | Topic |
|---|---|---|
| `presence-entree` | Présence oui/non | `maison/presence-entree/etat` |
| `temp-salon` | Température °C | `maison/temp-salon/temperature` |
| `temp-chambre` | Température °C | `maison/temp-chambre/temperature` |
| `temp-cuisine` | Température °C | `maison/temp-cuisine/temperature` |

Il n'y a pas de vrai matériel : les mesures sont générées en Python. Le superviseur affiche les résultats dans le terminal, sans interface web. Le traitement reste local, sans cloud.

## Architecture

```text
Capteurs simulés (x4)
        |
        | MQTT v5 + mTLS
        v
  Broker Mosquitto
   (ACL par topic)
        |
        | MQTT v5 + mTLS
        v
 Superviseur Python
    |         |
 Mesures    Alertes
```

Tous les services sont dans le réseau Docker `maison-privee`. Aucun port du broker n'est publié sur l'ordinateur hôte.

## Démarrage sur Ubuntu

Prévoir Docker Engine et `docker compose` (version 2). Au premier démarrage, une connexion Internet est nécessaire pour récupérer les images et les dépendances Python.

```bash
git clone https://github.com/bentibi/iot401-domotique.git
cd iot401-domotique
docker compose up --build -d
docker compose ps
docker compose logs --tail=30 superviseur
```

L'initialisation PKI se termine normalement avec `Exited (0)` : ce n'est pas une erreur. Les certificats sont créés dans des volumes Docker et ne doivent pas être ajoutés à Git.

Si Docker refuse l'accès, vérifier les droits Docker de l'utilisateur (ou préfixer les commandes Docker par `sudo`).

## Tests

Tests unitaires :

```bash
python3 -m unittest discover -s tests -v
```

Tests sur le broker (les conteneurs doivent être démarrés) :

```bash
docker compose run --rm audit-sans-certificat
docker compose run --rm audit-acl
docker compose run --rm audit-intrusion
docker compose run --rm audit-seuil
docker compose logs --tail=60 superviseur
```

Résultats attendus :

| Test | Ce qu'on vérifie |
|---|---|
| Sans certificat | Le broker coupe la connexion (mTLS). |
| ACL | `temp-salon` ne peut pas publier sur le topic de la chambre : `RC:135`. |
| Intrusion | `capteur-test` est détecté hors de la liste des quatre capteurs. |
| Seuil | `35.5 °C` provoque l'alerte de température. |

Ces tests ont réussi sur l'Ubuntu de Benjamin le **28 octobre 2026**. Les fichiers texte correspondants sont conservés dans `preuves/`. Une capture d'Ilias montre la réception des quatre capteurs sur son ordinateur. Les tests de sécurité sur son PC ne sont pas encore documentés.

## Ce qui sécurise la chaîne

- **Certificats :** une autorité locale crée un certificat par capteur, un pour le broker et un pour le superviseur (`app/pki.py`).
- **mTLS :** les clients vérifient le certificat du broker et le broker exige un certificat client (`app/commun.py`, `mosquitto/mosquitto.conf`).
- **ACL :** chaque capteur n'écrit que sur son topic ; le superviseur est le seul à pouvoir lire tous les topics (`mosquitto/acl.conf`).
- **Réseau :** le broker reste dans le réseau interne Docker (`compose.yaml`).
- **Vie privée :** les messages ne contiennent aucun nom ou image et ne partent pas sur Internet.

Pour tester la détection, `capteur-test` a volontairement un certificat accepté par le broker. Il est seulement inconnu du superviseur. En dehors des tests, un véritable objet non provisionné serait rejeté avant publication.

## Notre démarche

Nous avons d'abord fait fonctionner les capteurs et le superviseur. Ensuite, nous avons ajouté les certificats et les permissions MQTT, puis testé ce qui se passe quand un appareil ne respecte pas les règles.

Nous avons rencontré deux problèmes pendant les essais : Docker refusait une configuration de ses journaux, puis Mosquitto signalait des permissions incorrectes sur son fichier ACL. Ilias a corrigé la configuration Docker et intégré les fichiers Mosquitto dans l'image du broker avec les bons droits. Nous avons ensuite relancé les tests sur Ubuntu.

Pour revoir rapidement les tests principaux :

```bash
bash scripts/tester-projet.sh
```

Ilias a également ajouté `scripts/verifier-securite.sh`, qui examine plus de cas (certificat signé par une autre autorité, nom du serveur, secrets, etc.). C'est un contrôle complémentaire : il ne remplace pas les quatre preuves demandées par le sujet.

Le détail des difficultés rencontrées figure dans `docs/JOURNAL_DU_PROJET.md`.

## Dossier et limites

Le dossier d'examen se trouve dans `docs/dossier-IOT401.pdf`. Les mécanismes et questions pour l'oral sont expliqués dans `docs/EXPLICATIONS.md`.

Le prototype **ne contient pas** de matériel physique, de révocation individuelle des certificats, de secure boot ou de mise à jour OTA signée. Les clés privées ne sont pas chiffrées au repos dans les volumes Docker. Les logs sont limités par taille et non supprimés automatiquement après une durée précise. Ces limites sont détaillées dans le dossier.

## Contributions

Voir `CONTRIBUTIONS_A_COMPLETER.md` et l'historique Git. Les contributions et la page de signatures doivent être relues par les deux membres avant remise. Un commit indique qui a publié un fichier, pas automatiquement qui l'a écrit intégralement.

## Arrêt

```bash
docker compose down
```

Ne pas lancer `docker compose down -v` pour un arrêt normal : l'option `-v` supprime aussi les volumes contenant les certificats.

## Références

- Sujet, barème et gabarit IOT401 (Marouane El Moufid, 28/10/2026).
- ETSI EN 303 645 : https://www.etsi.org/
- OWASP IoT Top 10 : https://owasp.org/projects/internet-of-things/
- CRA (règlement UE 2024/2847) : https://eur-lex.europa.eu/eli/reg/2024/2847/oj
- CNIL, minimisation des données : https://www.cnil.fr/fr/minimiser-les-donnees-collectees
