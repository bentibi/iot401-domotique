# Mettre le projet sur GitHub à deux

**Dépôt visé :** `bentibi/iot401-domotique` (public pour le portfolio)  
**Binôme :** Benjamin TIBI et Ilias EL HOUZI (`SaitamaDuBled`).

## 1. Benjamin crée le dépôt et invite Ilias

Sur le PC Ubuntu de Benjamin :

```bash
sudo apt update
sudo apt install -y git gh
unzip ~/Téléchargements/IOT401_Benjamin_Depot_Initial.zip -d ~/Projets
cd ~/Projets/Benjamin_depot_initial
gh auth login
bash scripts/creer-depot-et-inviter.sh
```

Le script refuse de se lancer si la session GitHub n'est pas celle de `bentibi`,
pour éviter la création sur le mauvais compte. Il vérifie aussi la configuration
Git, vérifie que les clés ne sont pas dans les fichiers ajoutés et crée un
premier commit limité à la partie de Benjamin. Il appelle GitHub pour inviter
`SaitamaDuBled` en tant que collaborateur avec droit d'écriture.

**L'invitation n'est pas acceptée automatiquement.** Ilias doit l'accepter depuis
son compte (notification GitHub ou e-mail associé).

## 2. Ilias ajoute ses fichiers depuis son PC et son compte

Envoyer le fichier `IOT401_Ilias_Partie_A_Pousser.zip` à Ilias. Il doit
installer Git et GitHub CLI, puis s'authentifier avec `gh auth login`.

```bash
unzip ~/Téléchargements/IOT401_Ilias_Partie_A_Pousser.zip -d ~/Projets
bash ~/Projets/Ilias_a_pousser/publier-partie-ilias.sh
```

Le script utilise le compte GitHub connecté, clone le dépôt, copie uniquement
les fichiers attribués à Ilias et affiche les changements. **Il lui demande de
confirmer qu'il les a étudiés, validés et adaptés si nécessaire avant le commit.**
Il pousse ensuite un commit sous son propre compte Git.

Les fichiers attribués à Ilias sont :

```text
compose.yaml
app/Dockerfile
app/requirements.txt
app/commun.py
app/capteur.py
app/pki.py
mosquitto/mosquitto.conf
mosquitto/acl.conf
scripts/verifier-archive.sh
```

## 3. Intégration et preuves (ensemble)

Après le commit d'Ilias, Benjamin récupère la partie commune :

```bash
cd ~/Projets/Benjamin_depot_initial
git pull --ff-only
docker compose up --build -d
docker compose ps
python3 -m unittest discover -s tests -v
```

Puis les scénarios d'audit :

```bash
docker compose run --rm audit-sans-certificat
docker compose run --rm audit-acl
docker compose run --rm audit-intrusion
docker compose run --rm audit-seuil
docker compose logs --tail=40 superviseur
```

Mettre les captures réellement obtenues dans `preuves/` et modifier `.gitignore`
si vous souhaitez les publier sur GitHub : par défaut, il exclut les captures.
Ne jamais committer de clés privées, `.pem`, `.key` ou secrets.

## 4. Contrôler l'historique GitHub

```bash
git log --all --format='%h | %an <%ae> | %s' --date=short
```

Vérifier sur GitHub la présence de vrais commits de chacun. Un commit ne prouve
pas à lui seul la réalisation d'une tâche : mettez à jour
`CONTRIBUTIONS_A_COMPLETER.md` selon le travail **effectivement** réalisé, puis
complétez et signez la section 7 du dossier PDF ensemble.

**Attention :** le dépôt GitHub facilite la traçabilité, mais n'annule pas
l'obligation de rendre le ZIP et le PDF sur Classroom.
