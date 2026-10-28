# Travailler à deux sur notre dépôt GitHub

Dépôt : `bentibi/iot401-domotique`  
Benjamin : `bentibi`  
Ilias : `SaitamaDuBled`

Le dépôt existe déjà et les deux membres y ont participé. Nous n'avons plus besoin des archives de création du dépôt utilisées au début du projet.

## Méthode suivie

Chaque membre travaille sur ses fichiers, lance les tests correspondants, puis pousse un commit depuis son propre compte. Avant de modifier des fichiers partagés :

```bash
git pull --ff-only origin main
git status
```

Après les modifications :

```bash
git diff --check
git diff
# Puis ajouter uniquement les fichiers réellement modifiés.
git add chemin/vers/le/fichier
git commit -m "Description du changement"
git push origin main
```

Si Git signale un conflit, ne pas forcer le push et ne pas réécrire l'historique : il faut comparer les versions et régler le conflit.

## Qui travaille sur quoi ?

| Benjamin | Ilias |
|---|---|
| CDC, dossier, documentation | Capteurs, certificats, broker |
| Superviseur et scénarios d'audit | Docker Compose, réseau et ACL |
| Tests sur son Ubuntu et conservation des résultats | Vérification sur son Ubuntu, corrections Docker |

Les deux relisent la documentation et les contributions avant remise. Les détails sont dans `CONTRIBUTIONS_A_COMPLETER.md`.

## Vérifier l'historique

```bash
git log --format='%h | %an | %s' -8
```

Un commit permet d'identifier **qui a validé et publié** une modification. Il ne prouve pas à lui seul qui a écrit chaque ligne du fichier. La page des contributions doit représenter le travail réel.
