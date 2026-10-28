# IOT401 - Maison connectée sécurisée

Projet de domotique du module **Internet des objets (IOT401)**, École 2600.

**Binôme :** Benjamin TIBI et Ilias EL HOUZI (`SaitamaDuBled`)  
**Enseignant :** Marouane El Moufid  
**Cas :** Domotique | **Priorité :** vie privée

## Travail à deux sur GitHub

Le dépôt est volontairement créé en deux étapes afin que chacun puisse publier
**ses propres fichiers et les changements qu'il a effectivement contrôlés**.

- **Benjamin** : première mise en place du dépôt, superviseur, scénarios d'audit,
  tests Python, cahier des charges et dossier.
- **Ilias** (`SaitamaDuBled`) : capteurs simulés, paramètres MQTT, Mosquitto,
  certificats et mTLS, Docker Compose et vérification d'archive.
- **À deux** : démarrage de la chaîne, correction des erreurs, captures de preuves,
  analyse STRIDE, relecture et validation du dossier.

**Important :** après le premier commit de Benjamin, il manque volontairement
les fichiers d'Ilias. Les commandes `docker compose` ne fonctionneront qu'après
l'ajout des fichiers d'Ilias. Le dépôt GitHub enregistre les *commits*, pas la
preuve automatique de qui a conçu chaque ligne : chacun doit relire, tester et
assumer les fichiers qu'il pousse.

Voir `GITHUB_BINOME.md` et `CONTRIBUTIONS_A_COMPLETER.md`.

## Objectif

Simuler quatre capteurs domestiques. Ils publient leurs mesures sur MQTT **chiffré et authentifié des deux côtés (mTLS)**. Le broker Mosquitto vérifie les certificats et les autorisations par topic. Le superviseur lit les mesures, détecte les températures trop élevées et signale les objets inconnus.

| Identité du certificat (CN) | Mesure | Topic publié | Alimentation envisagée |
|---|---|---|---|
| `presence-entree` | Présence oui/non | `maison/presence-entree/etat` | Pile |
| `temp-salon` | Température °C | `maison/temp-salon/temperature` | Pile |
| `temp-chambre` | Température °C | `maison/temp-chambre/temperature` | Pile |
| `temp-cuisine` | Température °C | `maison/temp-cuisine/temperature` | Secteur |

Toutes les mesures sont **simulées** : aucun capteur physique ni pile n'est nécessaire. Les alimentations du tableau concernent l'architecture réelle envisagée.

## Architecture

```text
     ZONE 1 - LOGEMENT / CAPTEURS SIMULÉS
     presence-entree    temp-salon    temp-chambre    temp-cuisine
               \          |           |          /
                \         | MQTT v5 / mTLS      /
                 --------------------------------
                               |
                 [LIMITE DE CONFIANCE : CERTIFICATS + ACL]
                               |
                     Mosquitto (port 8883)
                           réseau privé
                      (aucun port publié)
                               |
                 [LIMITE DE CONFIANCE : LECTURE]
                               |
                    Superviseur Python (edge)
                    /        |            \
             mesures    seuil > 30 °C    objet inconnu
```

Le protocole de transport du prototype est **TCP/IP sur réseau Docker privé** et le protocole applicatif est **MQTT v5 sur TLS**. Dans une installation physique, on pourrait utiliser Wi-Fi ou Zigbee + passerelle selon la portée, le coût et l'autonomie. Le prototype ne prétend pas simuler une radio Zigbee ou une pile physique.

## Prérequis pour Ubuntu

- Docker Engine installé et démarré ;
- plugin **Docker Compose v2** (`docker compose version`) ;
- accès Internet au *premier* démarrage pour récupérer les images et les paquets Python ;
- pas besoin d'installer Python, OpenSSL ou Mosquitto sur le PC.

Vérification :

```bash
docker --version
docker compose version
docker info
```

Si la permission Docker est refusée, utiliser `sudo docker compose ...` ou configurer le groupe Docker conformément à la documentation Docker (l'appartenance au groupe Docker confère des privilèges élevés).

## 1. Démarrer le projet

Depuis le dossier contenant `compose.yaml` :

```bash
docker compose up --build -d
docker compose ps
docker compose logs --tail=40 superviseur
```

Le service `initialisation-pki` génère automatiquement l'autorité de certification et les certificats au premier démarrage, **uniquement dans des volumes Docker**. Les services attendent que cette initialisation soit terminée. Les clés ne se trouvent pas dans les sources ni dans Git.

La génération est persistante : `docker compose down` conserve les volumes pour les démarrages suivants. La commande `docker compose down -v` **supprime toutes les clés de la maquette** et force une nouvelle PKI au démarrage suivant.

Pour suivre la chaîne en temps réel :

```bash
docker compose logs -f --tail=20 superviseur
```

Exemple de résultat attendu (les valeurs sont aléatoires) :

```text
[SUPERVISEUR] écoute maison/#
[MESURE] maison/temp-salon/temperature : 22.5 °C
[MESURE] maison/temp-chambre/temperature : 20.1 °C
[MESURE] maison/presence-entree/etat : non
[MESURE] maison/temp-cuisine/temperature : 24.6 °C
```

## 2. Exécuter et capturer les preuves d'audit

**Exécuter ces commandes sur l'Ubuntu et enregistrer leurs véritables sorties.**

### Preuve A - Rejet sans certificat client (mTLS)

```bash
docker compose run --rm audit-sans-certificat
docker compose logs --tail=20 broker
```

Attendu : message `[PREUVE mTLS] OK`, connexion coupée par le serveur car le certificat client manque. Sur le broker, rechercher les erreurs TLS si elles sont présentes.

### Preuve B - ACL : refus d'écrire sur le topic d'un autre capteur

```bash
docker compose run --rm audit-acl
```

Le capteur `temp-salon` utilise son propre certificat, mais tente d'écrire sur `maison/temp-chambre/temperature`. Le code attend un PUBACK MQTT v5 **`RC:135` (Not authorized)**. Un autre code entraîne un échec du test.

### Preuve C - Objet inconnu (hors liste blanche)

```bash
docker compose run --rm audit-intrusion
docker compose logs --tail=25 superviseur
```

Attendu : publication acceptée par le broker pour le **certificat de démonstration** `capteur-test`, puis affichage `[ALERTE INTRUSION] Objet inconnu : topic=maison/capteur-test/etat` dans le superviseur.

**Nuance importante :** `capteur-test` a volontairement été provisionné dans la PKI et autorisé sur son seul topic pour rendre ce cas d'audit reproductible. Il n'est **pas** dans la liste des quatre objets autorisés par le superviseur. En production, on ne donnerait pas de certificat actif à un dispositif inconnu. Les ACL empêchent déjà un objet non provisionné d'entrer.

### Preuve D - Dépassement du seuil

```bash
docker compose run --rm audit-seuil
docker compose logs --tail=25 superviseur
```

Attendu : `[ALERTE SEUIL] maison/temp-salon/temperature : 35.5 °C > 30.0 °C`.

### Preuve E - Broker non exposé

```bash
docker compose ps
docker network ls
```

Attendu : **aucune publication de port** sur le broker (pas de `0.0.0.0:8883->8883`). Le réseau `maison-privee` est déclaré `internal: true` dans `compose.yaml`. Attention : cette isolation ne protège pas d'une compromission de l'hôte Docker.

Les captures réelles sont décrites dans `preuves/README.md`. Elles ne sont **pas fournies artificiellement** dans ce dépôt.

## Tester les règles sans Docker

On peut vérifier séparément les règles du superviseur avec Python installé sur le PC :

```bash
python3 -m unittest discover -s tests -v
```

Ces cinq tests contrôlent une température normale, le seuil, la présence, un objet inconnu et un format incorrect. Ils ne remplacent **pas** les quatre preuves MQTT/mTLS à réaliser avec Docker.

## Explication du projet

Le fichier `docs/EXPLICATIONS.md` récapitule le rôle de chaque programme et les choix de sécurité. Il sert aussi à préparer une présentation orale à deux.

## 3. Arrêter / réinitialiser

```bash
# Arrêt normal (garde les certificats)
docker compose down

# Réinitialisation complète de la maquette (détruit les certificats)
docker compose down -v
```

Ne pas utiliser `down -v` pour une simple pause : les identités seront recréées et les anciens certificats seront invalidés.

## Choix de sécurité

| Choix | Où le vérifier |
|---|---|
| CA privée, un certificat serveur, un certificat par client | `app/pki.py` |
| Certificat client exigé par le broker | `mosquitto/mosquitto.conf` : `require_certificate true` |
| CN X.509 utilisé comme identité MQTT | `mosquitto/mosquitto.conf` : `use_identity_as_username true` |
| Vérification de l'identité TLS du serveur `broker` | `app/commun.py` : `check_hostname=True`, `CERT_REQUIRED` |
| Permissions de publication par capteur | `mosquitto/acl.conf` |
| Un volume de clés séparé par conteneur | `compose.yaml` |
| Pas d'exposition réseau sur l'hôte | `compose.yaml` : aucun `ports:`, réseau interne |
| Detection hors liste blanche | `app/superviseur.py` : `SUJETS_AUTORISES` |
| Règle de température `>30 °C` | `app/superviseur.py` |
| Pas de conservation des messages par Mosquitto | `persistence false`, QoS 1, `retain=False` |

### Limites et confidentialité

- La présence est une **donnée personnelle potentielle** ; la mesure est seulement un booléen. Aucun nom, image, localisation GPS ou identifiant d'occupant n'est envoyé.
- Le traitement est local (edge), sans serveur cloud ni base de données. Les logs du conteneur peuvent toutefois contenir des mesures : Docker conserve des journaux avec **rotation par taille**, pas une durée fixe en heures. Pour un usage réel, il faudrait une politique de purge datée et documentée.
- Les clés privées ne sont pas chiffrées **dans les volumes de la maquette** ; elles ont des permissions restreintes et des volumes cloisonnés, mais un administrateur Docker/host peut toujours y accéder. Pour des objets physiques : TPM/secure element, disque chiffré, sauvegardes chiffrées.
- Certificats de démonstration de 90 jours, CA 365 jours. La rotation et la révocation sélective (CRL/OCSP) ne sont pas implémentées ; suppression des volumes + réémission de la CA = révocation globale de la maquette.
- Secure boot, OTA signé et anti-rollback sont documentés comme **améliorations**, pas implémentés par ce prototype de capteurs logiciels.
- Le CN d'un émetteur n'est pas transporté dans le message MQTT reçu. La détection « objet inconnu » repose sur **un topic non répertorié**, en s'appuyant sur la correspondance imposée par les ACL. Elle ne remplace pas une vérification d'identité côté application.
- La présence aléatoire n'est pas une détection humaine réelle. L'alimentation pile/secteur, Wi-Fi et Zigbee sont des contraintes de conception, non implémentées.

## Structure du dépôt

```text
.
├── compose.yaml
├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pki.py              # création CA, broker et clients
│   ├── commun.py           # TLS + MQTT commun
│   ├── capteur.py          # 4 instances du même simulateur
│   ├── superviseur.py      # mesures, seuil, allowlist
│   └── audit.py            # scénarios de preuve
├── mosquitto/
│   ├── mosquitto.conf
│   └── acl.conf
├── docs/
│   ├── dossier-IOT401.pdf
│   └── EXPLICATIONS.md
├── preuves/
│   └── README.md           # captures à effectuer sur Ubuntu
├── tests/
│   └── test_superviseur.py
├── scripts/
│   └── verifier-archive.sh
└── CONTRIBUTIONS_A_COMPLETER.md
```

## Publication et historique de contributions

Sur Ubuntu, utiliser `bash scripts/creer-depot-et-inviter.sh` dans le dossier de
Benjamin après avoir fait `gh auth login`. Le script crée le dépôt public
`bentibi/iot401-domotique`, pousse les fichiers de Benjamin et envoie une
invitation de collaborateur à `SaitamaDuBled`. Le compte invité doit accepter
l'invitation avant de pousser ses fichiers.

Le document `GITHUB_BINOME.md` explique l'ordre des étapes et les commits attendus.
Le dossier final et les preuves réelles restent à déposer sur Classroom selon
les consignes de l'enseignant.

## Références

- Sujet de l'examen IOT401 et barème de Marouane El Moufid (28 octobre 2026).
- ETSI EN 303 645, sécurité des objets IoT grand public : https://www.etsi.org/deliver/etsi_en/303600_303699/303645/03.01.02_20/en_303645v030102a.pdf
- OWASP IoT Top 10 (2018) : https://owasp.org/projects/internet-of-things
- Cyber Resilience Act, règlement UE 2024/2847 : https://eur-lex.europa.eu/eli/reg/2024/2847/oj
- CNIL, minimisation : https://www.cnil.fr/fr/minimiser-les-donnees-collectees
- Documentation Eclipse Mosquitto : https://mosquitto.org/man/mosquitto-conf-5.html
