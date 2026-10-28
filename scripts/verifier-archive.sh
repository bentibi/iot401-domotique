#!/usr/bin/env bash
# Contrôle basique avant publication publique / dépôt Classroom.
set -euo pipefail
cd "$(dirname "$0")/.."

echo '[1/3] Contrôle des fichiers ajoutés à Git'
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git ls-files | grep -Ei '\.(key|p12|pfx|pem)$|(^|/)certs?/' && {
    echo 'ERREUR: fichiers sensibles suivis par Git'; exit 1;
  } || true
fi

echo '[2/3] Contrôle de la structure'
for f in compose.yaml mosquitto/mosquitto.conf mosquitto/acl.conf app/pki.py app/capteur.py app/superviseur.py app/audit.py README.md; do
  test -f "$f" || { echo "MANQUANT: $f"; exit 1; }
done

echo '[3/3] Contrôle des secrets privés dans les sources'
if grep -RIl --include='*.py' --include='*.yaml' --include='*.conf' --include='*.md' -- '-----BEGIN .*PRIVATE KEY-----' .; then
  echo 'ERREUR: clé privée détectée'; exit 1
fi

echo 'OK : structure présente, pas de clé PEM littérale détectée.'
