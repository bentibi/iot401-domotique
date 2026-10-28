#!/usr/bin/env bash
# Les tests que nous avons utilisés pour valider notre maison connectée.
set -euo pipefail
cd "$(dirname "$0")/.."

echo '1. Démarrage des conteneurs'
docker compose config -q
docker compose up --build -d
sleep 15

echo '2. Tests du superviseur'
python3 -m unittest discover -s tests -v

echo '3. Tests MQTT'
for test in audit-sans-certificat audit-acl audit-intrusion audit-seuil; do
    echo "Test : $test"
    docker compose run --rm -T "$test"
done

echo '4. Alertes observées'
logs=$(docker compose logs --no-color --tail=200 superviseur)
grep -F '[ALERTE INTRUSION]' <<< "$logs"
grep -F '[ALERTE SEUIL]' <<< "$logs"

echo '5. Conteneurs'
docker compose ps
echo 'Fin des tests : toutes les étapes ont réussi.'
