# Comprendre notre projet IOT401

## 1. L'idée du projet

Nous simulons quatre objets dans une maison : un détecteur de présence à l'entrée, un thermomètre dans le salon, un dans la chambre et un dans la cuisine. Chaque capteur publie une mesure toutes les 8 à 10 secondes sur un sujet MQTT différent. Le superviseur lit les quatre sujets et affiche une alerte si une température dépasse 30 °C. Il signale aussi un sujet MQTT qui ne fait pas partie de notre liste.

Les mesures sont inventées par Python, aucun vrai capteur n'est nécessaire. Nous n'avons pas créé une interface graphique : le tableau de bord du prototype correspond aux messages du superviseur dans le terminal.

## 2. Le chemin suivi par une mesure

1. `app/capteur.py` choisit une valeur, par exemple `22.5`, puis l'envoie à `maison/temp-salon/temperature`.
2. La connexion au broker `Mosquitto` est chiffrée par TLS. Le capteur et le broker vérifient leurs certificats (mTLS).
3. Le broker vérifie l'identité du capteur et ses permissions dans `mosquitto/acl.conf`.
4. `app/superviseur.py` est abonné à `maison/#` : il reçoit la mesure et vérifie le seuil et la liste des sujets autorisés.
5. Le résultat s'affiche dans le terminal avec `docker compose logs superviseur`.

## 3. À quoi servent les fichiers ?

| Fichier | Rôle |
|---|---|
| `compose.yaml` | Démarrer le broker, les 4 capteurs, le superviseur et les outils de test dans Docker. |
| `app/capteur.py` | Simuler un capteur et envoyer les mesures. |
| `app/commun.py` | Créer une connexion MQTT v5 avec vérification du certificat serveur. |
| `app/superviseur.py` | Afficher les données et les alertes. |
| `app/pki.py` | Générer l'autorité de certification et un certificat distinct par service. |
| `mosquitto/mosquitto.conf` | Exiger TLS et le certificat client pour chaque connexion. |
| `mosquitto/acl.conf` | Autoriser chaque capteur à publier uniquement sur son sujet. |
| `app/audit.py` | Tester le refus sans certificat, le refus ACL, l'intrusion et le seuil. |
| `tests/test_superviseur.py` | Vérifier cinq règles Python, même sans Docker. |
| `docs/dossier-IOT401.pdf` | Dossier au plan demandé : CDC, architecture, sécurité, audit, conformité, limites et contributions. |

## 4. Les quatre mécanismes à savoir expliquer

**mTLS :** le broker montre son certificat au capteur, et le capteur montre le sien au broker. Aucun client ne peut se connecter sans certificat valide signé par notre CA.

**ACL :** être authentifié ne donne pas tous les droits. Par exemple, `temp-salon` peut écrire sur `maison/temp-salon/temperature`, mais pas sur celui de `temp-chambre`. Le test de refus attend le code MQTT v5 `135`.

**Segmentation Docker :** le broker n'a pas de port publié vers le PC. Seuls les conteneurs connectés au réseau privé Docker peuvent l'atteindre. L'hôte Docker reste une zone de confiance importante.

**Liste blanche :** le superviseur ne connaît que quatre sujets. Pour montrer une intrusion dans un laboratoire qui impose mTLS, un certificat spécial `capteur-test` est créé. Il est techniquement autorisé par le broker, mais pas reconnu par le superviseur : cela déclenche l'alerte. Ce n'est pas un vrai attaquant anonyme qui franchit mTLS.

## 5. Ce qu'on doit montrer au professeur

On ne se contente pas d'affirmer que la sécurité existe : il faut l'exécuter. Les commandes sont détaillées dans le README. Il faut conserver les captures :

- une mesure par capteur vue dans le superviseur ;
- un refus de connexion sans certificat ;
- un refus de publication sur un autre sujet, avec `RC:135` ;
- l'alerte pour `capteur-test` ;
- l'alerte pour une température de 35,5 °C ;
- la preuve qu'aucun port du broker n'est publié sur le PC.

Les cinq tests unitaires Python sont déjà passés dans l'environnement de préparation. **Nous n'avons pas de moteur Docker dans cet environnement : les tests de bout en bout doivent encore être exécutés sur l'Ubuntu du binôme.**

## 6. Pourquoi la vie privée est prioritaire

Une mesure de présence peut indiquer quand les habitants rentrent ou sortent. Nous envoyons donc seulement `true` ou `false`, sans image ni nom. Toutes les données sont traitées localement. Les logs Docker restent cependant consultables tant qu'ils ne sont pas supprimés : le prototype ne garantit pas encore une durée de rétention définie en heures.

## 7. Ce qu'on n'a pas fait

Il n'y a pas de vraie sonde, de réseau Zigbee, de secure boot, de mise à jour OTA, ni de révocation individuelle des certificats. Ces pistes sont expliquées dans le PDF. Les contributions et signatures restent à compléter selon le travail réellement effectué par chacun.

## 8. Questions possibles à l'oral

**Pourquoi MQTT plutôt que HTTP ?** Parce que des capteurs envoient de petites mesures fréquemment, et que MQTT est adapté au modèle publication/abonnement.

**Quelle différence entre TLS et mTLS ?** En TLS classique, le client vérifie surtout l'identité du serveur ; en mTLS, le serveur vérifie aussi le certificat du client.

**Pourquoi un certificat différent par capteur ?** Pour identifier chaque objet et lui donner des droits limités, sans partager une seule identité.

**Pourquoi MQTT v5 ?** Nous récupérons notamment les raisons de refus des publications, dont `RC:135`, pour notre audit.

**Pourquoi ne pas garder les données dans une base ?** Notre objectif est la supervision instantanée, et limiter la conservation des données est cohérent avec la protection de la vie privée.
