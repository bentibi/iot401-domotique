# Nos preuves de fonctionnement

Tous les résultats ci-dessous viennent des essais sur Ubuntu, le 28 octobre 2026.

| Fichier | Ce qu'on voit |
|---|---|
| `preuve-infrastructure.txt` | Conteneurs Docker démarrés. |
| `preuve-chaine.txt` | Réception des quatre mesures dans le superviseur. |
| `preuve-tests-unitaires.txt` | Cinq tests Python réussis. |
| `preuve-audit-sans-certificat.txt` | Le broker coupe la connexion sans certificat. |
| `preuve-audit-acl.txt` | Publication interdite refusée, `RC:135`. |
| `preuve-audit-intrusion.txt` | Publication acceptée pour `capteur-test`, volontairement hors allowlist. |
| `preuve-audit-seuil.txt` | Envoi d'une mesure de 35,5 °C. |
| `preuve-alertes.txt` | Les alertes intrusion et seuil dans le superviseur. |
| `fonctionnement-superviseur-ilias.png` | Capture du fonctionnement sur le deuxième PC. |

**Pour le rendu :** ajouter aussi des captures de terminal des tests mTLS, ACL et intrusion (ou un enregistrement de session), comme le demande le sujet. Les fichiers texte seuls ne remplacent pas cette obligation.

Attention : le test intrusion utilise un capteur de démonstration muni d'un certificat. Il teste la liste blanche du superviseur, pas le contournement de mTLS.
