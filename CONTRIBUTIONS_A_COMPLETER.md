# Travail en binôme : IOT401 Domotique

**Binôme :** Benjamin TIBI (`bentibi`) et Ilias EL HOUZI (`SaitamaDuBled`).

Le tableau donne la **répartition prévue**, pas une attestation de travail terminé.
On complètera la colonne « validation » et la section de signatures du PDF
**après les tests réels**.

| Travail prévu | Responsable principal | Validation / preuve à joindre |
|---|---|---|
| Choix des quatre capteurs, CDC, schéma | Benjamin | Validation commune du cahier des charges |
| Simulations température et présence | Ilias | Logs des quatre capteurs |
| Connexion MQTT/TLS partagée | Ilias | Tests de connexion |
| Mosquitto, ACL et PKI/mTLS | Ilias | Refus sans certificat et RC 135 |
| Docker Compose, conteneurs, réseau | Ilias | `docker compose ps` |
| Superviseur et alertes | Benjamin | Logs seuil et intrusion |
| Tests Python et scénarios d'audit | Benjamin | Tests unitaires et essais Docker |
| Contrôles archive / secrets | Ilias | Sortie du script de vérification |
| STRIDE, conformité et dossier | Benjamin (premier jet) | Relecture et validation par Ilias |
| Intégration, correction, captures, présentation | Ensemble | Vérification finale ensemble |

## Convention des commits

Chacun commit **sur son propre compte** et indique une tâche précise :

- `Ajout du superviseur et des scénarios d'audit` (Benjamin)
- `Ajout des capteurs, de Mosquitto et du mTLS` (Ilias)
- `Tests de la chaîne MQTT et captures de preuves` (auteur ayant fait ces tests)
- `Corrections après intégration` (auteur des corrections)

Un commit poussé par un compte ne constitue pas à lui seul une preuve d'écriture
originale. Les contributions doivent correspondre au travail réellement mené.

## Vérification finale (à remplir après exécution)

- Date de test : ____________________
- Commande de démarrage et résultat : ____________________
- Tests mTLS / ACL / intrusion / seuil : ____________________
- Commits des deux comptes vérifiés : ____________________
- Documentation relue et PDF signé : ____________________

Benjamin TIBI : ____________________  Date : __________

Ilias EL HOUZI : ___________________  Date : __________
