# Preuves à réaliser sur votre Ubuntu

Aucune capture n'est simulée ou inventée. Après l'exécution des commandes du README :

1. `preuve-chaine.png` : `docker compose logs --tail=20 superviseur`, mesures reçues.
2. `preuve-mtls.png` : `docker compose run --rm audit-sans-certificat` avec message de refus + éventuellement logs du broker.
3. `preuve-acl-rc135.png` : `docker compose run --rm audit-acl` et la ligne `RC:135`.
4. `preuve-intrusion.png` : `docker compose run --rm audit-intrusion` puis `docker compose logs --tail=20 superviseur` montrant l'alerte.
5. `preuve-seuil.png` : `docker compose run --rm audit-seuil` puis logs superviseur montrant >30 °C.
6. `preuve-segmentation.png` : `docker compose ps` (aucun port hôte exposé) + extrait compose réseau `internal: true`.

Conseil : utiliser l'outil Capture d'écran Ubuntu, sauvegarder ici les captures
et ajouter les captures à l'archive Classroom (pas nécessairement au GitHub public).
