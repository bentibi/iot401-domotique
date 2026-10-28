# Notre journal de projet - IOT401

**28 octobre 2026 - Mise en route.** Nous avons choisi de simuler une maison avec trois thermomètres et un capteur de présence. Les mesures sont publiées sur des topics MQTT différents.

**Premier blocage.** Docker refusait de créer les conteneurs : les options de compression des journaux n'étaient pas compatibles avec `max-file: 1`. Nous avons corrigé cette option et relancé la chaîne.

**Deuxième problème.** Mosquitto signalait des permissions incorrectes sur `acl.conf`. Ilias a modifié le Dockerfile du broker pour intégrer les fichiers de configuration avec leurs droits et exécuter le service sans root.

**Tests de Benjamin.** Nous avons vérifié cinq règles Python et quatre scénarios MQTT : refus sans certificat, publication hors ACL, topic inconnu et dépassement du seuil de température. Ces tests ont réussi sur l'Ubuntu de Benjamin, y compris après la correction Mosquitto.

**Vérification sur le deuxième PC.** La capture d'Ilias montre la réception des quatre capteurs sur son Ubuntu. Cela ne prouve pas, à lui seul, qu'il a lancé tous les tests de sécurité.

**Derniers éléments à fournir.** Captures des tests mTLS, ACL et intrusion, résultat du contrôle avancé si nous le présentons, relecture et signatures des contributions.

Nous avons utilisé des capteurs simulés : les résultats ne prouvent ni l'autonomie d'une batterie réelle, ni la portée d'un réseau radio.
