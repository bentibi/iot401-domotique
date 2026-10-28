# Explications du projet IOT401

## À quoi sert notre projet ?

Nous avons créé une maison connectée simulée avec quatre capteurs : trois températures et une présence. Chaque capteur transmet ses valeurs à Mosquitto. Le superviseur affiche les mesures et déclenche une alerte si la température dépasse 30 °C ou si un topic inconnu apparaît.

Le but du devoir n'était pas de fabriquer des objets physiques, mais de sécuriser les échanges entre objets IoT.

## Le chemin d'une mesure

1. `app/capteur.py` simule une valeur et la convertit en JSON : `{"valeur": 22.5}`.
2. `app/commun.py` prépare la connexion MQTT avec validation TLS.
3. Le broker Mosquitto vérifie le certificat du capteur et ses droits dans les ACL.
4. `app/superviseur.py` reçoit la mesure sur `maison/#` et vérifie les règles.
5. Le résultat se lit avec `docker compose logs superviseur`.

## À quoi servent les principaux fichiers ?

| Fichier | Utilité |
|---|---|
| `compose.yaml` | Démarre les conteneurs et leurs réseaux/volumes. |
| `app/capteur.py` | Simule les quatre capteurs. |
| `app/commun.py` | Réunit les paramètres MQTT et TLS communs. |
| `app/pki.py` | Crée l'autorité et les certificats. |
| `mosquitto/` | Contient la configuration du broker et les ACL. |
| `app/superviseur.py` | Affiche les mesures, les erreurs et les alertes. |
| `app/audit.py` | Exécute les quatre scénarios de test. |
| `tests/` | Vérifie les règles Python sans lancer Docker. |

## Ce qu'on a vraiment vérifié

Sur l'ordinateur de Benjamin le 28/10/2026 :

- les quatre capteurs envoient leurs mesures au superviseur ;
- les cinq tests unitaires passent ;
- sans certificat client, la connexion au broker est coupée ;
- `temp-salon` ne peut pas écrire sur le topic de `temp-chambre` (`RC:135`) ;
- un message de `capteur-test` déclenche l'alerte « objet inconnu » ;
- une température de 35,5 °C déclenche l'alerte de seuil.

Sur l'ordinateur d'Ilias, une capture montre également les quatre mesures dans les logs du superviseur. Les sorties des tests sont dans `preuves/`.

## Les notions à savoir expliquer

**MQTT :** protocole de messages en publication/abonnement, bien adapté aux petites mesures.

**TLS :** chiffre les échanges et permet au client de vérifier le serveur.

**mTLS :** le broker vérifie en plus le certificat du client. Notre autorité locale signe les certificats.

**CN :** nom inscrit dans un certificat et utilisé ici comme identité MQTT du capteur.

**ACL :** liste de droits. Avoir un certificat ne permet pas de publier n'importe où.

**Réseau interne Docker :** nos conteneurs communiquent entre eux, mais le broker n'a pas de port publié vers l'hôte. Ce n'est pas une protection contre un administrateur de l'hôte.

**Allowlist :** liste des quatre topics attendus par le superviseur. Le test `capteur-test` a volontairement un certificat pour pouvoir tester l'alerte applicative ; cela ne prouve pas qu'un objet inconnu traverse mTLS.

## Limites

Nous ne mesurons pas une vraie pièce. Nous n'avons pas implémenté de révocation sélective, secure boot, OTA signé ou purge des journaux après 24 h. Les clés restent dans des volumes Docker, sans chiffrement au repos ; l'administrateur Docker y a accès. Ces choix sont adaptés à une maquette pédagogique, pas à un produit prêt à commercialiser.

Le document PDF contient le cahier des charges, l'analyse STRIDE, l'arbre d'attaque et les rapports d'audit et de conformité.
