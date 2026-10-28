#!/usr/bin/env bash
# Création du dépôt et invitation d'Ilias depuis le compte de Benjamin.
set -euo pipefail
cd "$(dirname "$0")/.."
REPO="bentibi/iot401-domotique"
PARTENAIRE="SaitamaDuBled"

erreur() { printf 'ERREUR : %s\n' "$1" >&2; exit 1; }
command -v gh >/dev/null || erreur 'Installer GitHub CLI : sudo apt install gh'
command -v git >/dev/null || erreur 'Installer Git : sudo apt install git'
gh auth status >/dev/null 2>&1 || erreur 'Se connecter avec gh auth login'
COMPTE="$(gh api user --jq .login)"
[[ "$COMPTE" == "bentibi" ]] || erreur "Compte connecté : $COMPTE (attendu : bentibi)"
[[ -f app/superviseur.py && -f GITHUB_BINOME.md ]] || erreur 'Mauvais dossier ou fichiers manquants'
if [[ ! -d .git ]]; then
    git init -b main
fi
# Configuration Git locale pour rattacher les commits au compte GitHub connecté.
ID_GITHUB="$(gh api user --jq .id)"
git config user.name 'Benjamin TIBI'
git config user.email "${ID_GITHUB}+${COMPTE}@users.noreply.github.com"

git add .
# Pas de fichiers sensibles dans les éléments préparés.
if git diff --cached --name-only | grep -Ei '\.(key|pem|p12|pfx)$|(^|/)(certs?|certificats)/'; then
    erreur 'Clé ou répertoire de certificats détecté dans le commit.'
fi
# Interdire de faire passer les fichiers attribués à Ilias dans le commit initial.
for f in compose.yaml app/capteur.py app/commun.py app/pki.py app/Dockerfile mosquitto/acl.conf mosquitto/mosquitto.conf; do
    if git diff --cached --name-only | grep -Fxq "$f"; then
        erreur "Le fichier $f appartient au lot d'Ilias. Utiliser l'archive Benjamin."
    fi
done
if ! git rev-parse HEAD >/dev/null 2>&1; then
    git commit -m "Mise en place du projet et du superviseur domotique"
elif ! git diff --cached --quiet; then
    git commit -m "Mise à jour des fichiers de Benjamin"
fi

if gh repo view "$REPO" >/dev/null 2>&1; then
    echo "Dépôt existant : $REPO"
    git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://github.com/$REPO.git"
    git push -u origin main
else
    gh repo create "$REPO" --public --source=. --remote=origin --push
fi

echo "Envoi de l'invitation à $PARTENAIRE..."
gh api -X PUT "repos/$REPO/collaborators/$PARTENAIRE" -f permission=push >/dev/null
echo 'Demande envoyée : Ilias doit accepter son invitation pour pouvoir pousser.'
echo "Dépôt : https://github.com/$REPO"
echo 'Après acceptation, lui transmettre le ZIP contenant sa partie.'
