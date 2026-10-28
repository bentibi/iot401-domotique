#!/usr/bin/env bash
# Vérifie tous les points de sécurité attendus par le barème IOT401.
# Usage : bash scripts/verifier-securite.sh   (depuis la racine du dépôt)
# Prérequis : la chaîne a été démarrée une fois (docker compose up --build -d).
set -uo pipefail
cd "$(dirname "$0")/.."

# Utilise sudo seulement si l'utilisateur n'a pas accès à Docker.
DOCKER="docker"
docker info >/dev/null 2>&1 || DOCKER="sudo docker"
DC="$DOCKER compose"

VERT='\033[32m'; ROUGE='\033[31m'; JAUNE='\033[33m'; FIN='\033[0m'
REUSSIS=0; ECHECS=0
ok()    { printf "${VERT}[OK]${FIN}     %s\n" "$1"; REUSSIS=$((REUSSIS+1)); }
echec() { printf "${ROUGE}[ECHEC]${FIN}  %s\n" "$1"; ECHECS=$((ECHECS+1)); }
titre() { printf "\n${JAUNE}== %s ==${FIN}\n" "$1"; }
maintenant() { date -u +%Y-%m-%dT%H:%M:%SZ; }

# Exécute un petit programme Python dans le conteneur d'un service
# (donc avec le certificat de ce service monté dans /certs).
py_dans() {
    local service="$1"; shift
    $DC run --rm --no-deps -T "$service" python - "$@" 2>&1
}

# Programme Python commun aux essais de connexion.
read -r -d '' ESSAI <<'PYTHON'
import socket, ssl, sys, threading, time, json
import paho.mqtt.client as mqtt

mode = sys.argv[1]
HOTE, PORT = 'broker', 8883

def contexte(hostname=True, cert=None, cle=None):
    ctx = ssl.create_default_context(cafile='/certs/ca.crt')
    ctx.check_hostname = hostname
    ctx.verify_mode = ssl.CERT_REQUIRED
    if cert:
        ctx.load_cert_chain(cert, cle)
    return ctx

def connecter(ctx, hote=HOTE):
    """Renvoie 'connecte', 'refus-client' (le CLIENT a refusé le serveur),
    'refus-serveur' (le BROKER a refusé le client) ou 'injoignable'."""
    # Sans ce contrôle, une panne réseau passerait pour un refus du broker.
    try:
        socket.create_connection((hote, PORT), timeout=4).close()
    except OSError as e:
        return 'injoignable', str(e)
    connecte, coupe = threading.Event(), threading.Event()
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f'verif-{mode}', protocol=mqtt.MQTTv5)
    c.tls_set_context(ctx)
    c.on_connect = lambda cl, u, f, rc, p: (coupe if rc.is_failure else connecte).set()
    c.on_disconnect = lambda cl, u, f, rc, p: coupe.set()
    try:
        c.connect(hote, PORT, keepalive=10)
    except ssl.SSLCertVerificationError as e:
        return 'refus-client', str(e)
    except (OSError, ssl.SSLError) as e:
        return 'refus-serveur', str(e)
    c.loop_start()
    coupe.wait(6)
    c.loop_stop()
    if connecte.is_set() and not coupe.is_set():
        c.disconnect()
        return 'connecte', ''
    return ('refus-serveur', 'connexion coupée par le broker') if coupe.is_set() else ('inconnu', 'pas de réponse')

if mode == 'avec-certificat':
    print(*connecter(contexte(cert='/certs/client.crt', cle='/certs/client.key')))

elif mode == 'sans-certificat':
    print(*connecter(contexte()))

elif mode == 'certificat-etranger':
    # Certificat valide en apparence (CN légitime) mais signé par une AUTRE autorité.
    from datetime import datetime, timedelta, timezone
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    cle = ec.generate_private_key(ec.SECP256R1())
    nom = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'temp-salon')])
    t = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(nom).issuer_name(nom)
            .public_key(cle.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(t - timedelta(days=1)).not_valid_after(t + timedelta(days=1))
            .sign(cle, hashes.SHA256()))
    open('/tmp/faux.crt', 'wb').write(cert.public_bytes(serialization.Encoding.PEM))
    open('/tmp/faux.key', 'wb').write(cle.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    print(*connecter(contexte(cert='/tmp/faux.crt', cle='/tmp/faux.key')))

elif mode == 'mauvais-nom':
    # On joint le broker par son IP : le nom ne correspond plus au certificat serveur.
    ip = socket.gethostbyname(HOTE)
    print(*connecter(contexte(cert='/certs/client.crt', cle='/certs/client.key'), hote=ip))

elif mode == 'publier':
    topic = sys.argv[2]
    recu, fait = [], threading.Event()
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f'verif-pub-{time.time()}', protocol=mqtt.MQTTv5)
    c.tls_set_context(contexte(cert='/certs/client.crt', cle='/certs/client.key'))
    c.on_connect = lambda cl, u, f, rc, p: cl.publish(topic, json.dumps({'valeur': 20.0}), qos=1)
    c.on_publish = lambda cl, u, mid, rc, p: (recu.append(rc.value), fait.set())
    try:
        c.connect(HOTE, PORT, keepalive=10)
    except OSError as e:
        print('injoignable', e); sys.exit()
    c.loop_start()
    fait.wait(8)
    c.disconnect(); c.loop_stop()
    print('RC', recu[0] if recu else 'aucun')
PYTHON

essai() { py_dans "$1" "${@:2}" <<<"$ESSAI" | tail -1; }

# --------------------------------------------------------------------------
titre "0. Démarrage"
$DC up -d >/dev/null 2>&1
sleep 15
for s in broker superviseur presence-entree temp-salon temp-chambre temp-cuisine; do
    etat=$($DC ps --format '{{.State}}' "$s" 2>/dev/null)
    [[ "$etat" == "running" ]] && ok "service $s démarré" || echec "service $s : '${etat:-absent}'"
done

# --------------------------------------------------------------------------
titre "1. Chaîne complète capteur -> broker -> superviseur"
LOGS_SUP=$($DC logs --since 30s superviseur 2>&1)
for t in maison/presence-entree/etat maison/temp-salon/temperature maison/temp-chambre/temperature maison/temp-cuisine/temperature; do
    grep -q "\[MESURE\] $t" <<<"$LOGS_SUP" && ok "mesure reçue sur $t" || echec "aucune mesure récente sur $t"
done

# --------------------------------------------------------------------------
titre "2. Identité et mTLS"
r=$(essai temp-salon avec-certificat)
[[ "$r" == connecte* ]] && ok "témoin : connexion acceptée avec un certificat valide" \
                        || echec "le certificat valide est refusé : $r"

DEBUT=$(maintenant)
r=$(essai temp-salon sans-certificat)
case "$r" in
  refus-serveur*) ok "sans certificat : connexion refusée par le broker" ;;
  refus-client*)  echec "INCONCLUANT : c'est le client qui refuse le serveur ($r)" ;;
  *)              echec "sans certificat : connexion ACCEPTÉE ($r)" ;;
esac
sleep 1
$DC logs --since "$DEBUT" broker 2>&1 | grep -q "peer did not return a certificate" \
    && ok "log broker : 'peer did not return a certificate'" \
    || echec "log broker : refus du certificat absent non trouvé"

r=$(essai temp-salon certificat-etranger)
case "$r" in
  refus-serveur*) ok "certificat signé par une autre AC : refusé par le broker" ;;
  refus-client*)  echec "INCONCLUANT : c'est le client qui refuse le serveur ($r)" ;;
  *)              echec "certificat d'une autre AC ACCEPTÉ ($r)" ;;
esac

# --------------------------------------------------------------------------
titre "3. Validation du certificat serveur côté client (pas de tls_insecure)"
r=$(essai temp-salon mauvais-nom)
[[ "$r" == refus-client* ]] && ok "le client refuse un serveur dont le nom ne correspond pas" \
                            || echec "le client accepte un serveur au mauvais nom : $r"
# Les lignes de commentaire (« fichier:ligne:   # ... ») sont ignorées.
TROUVE=$(grep -RnE 'tls_insecure_set\(\s*True|CERT_NONE|check_hostname\s*=\s*False' app/*.py | grep -vE '^[^:]+:[0-9]+:\s*#')
if [[ -n "$TROUVE" ]]; then
    echec "désactivation de la vérification TLS trouvée : $TROUVE"
else
    ok "aucun tls_insecure / CERT_NONE / check_hostname=False dans app/"
fi

# --------------------------------------------------------------------------
titre "4. ACL par topic (moindre privilège)"
r=$(essai temp-salon publier maison/temp-salon/temperature)
# RC 0 = accepté ; RC 16 = accepté mais aucun abonné (superviseur arrêté).
[[ "$r" == "RC 0" || "$r" == "RC 16" ]] && ok "temp-salon publie sur son topic ($r)" || echec "temp-salon sur son topic : $r"
r=$(essai temp-salon publier maison/temp-chambre/temperature)
[[ "$r" == "RC 135" ]] && ok "temp-salon -> topic de temp-chambre refusé (RC:135)" || echec "attendu RC 135, obtenu : $r"
r=$(essai superviseur publier maison/temp-salon/temperature)
[[ "$r" == "RC 135" ]] && ok "le superviseur ne peut pas publier (RC:135)" || echec "superviseur en écriture : $r"

# --------------------------------------------------------------------------
titre "5. Segmentation réseau"
PUBLIES=$($DOCKER inspect --format '{{json .NetworkSettings.Ports}}' "$($DC ps -q broker)" 2>/dev/null)
grep -q '"HostPort"' <<<"$PUBLIES" && echec "le broker publie un port sur l'hôte : $PUBLIES" \
                                   || ok "aucun port du broker publié sur l'hôte"
for reseau in $($DOCKER inspect --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}' "$($DC ps -q broker)"); do
    [[ "$($DOCKER network inspect --format '{{.Internal}}' "$reseau")" == "true" ]] \
        && ok "réseau $reseau interne (pas de sortie vers l'extérieur)" \
        || echec "réseau $reseau non interne"
done

# --------------------------------------------------------------------------
titre "6. Détection par le superviseur"
DEBUT=$(maintenant)
$DC run --rm -T audit-intrusion >/dev/null 2>&1
$DC run --rm -T audit-seuil >/dev/null 2>&1
sleep 2
LOGS_SUP=$($DC logs --since "$DEBUT" superviseur 2>&1)
grep -q "\[ALERTE INTRUSION\]" <<<"$LOGS_SUP" && ok "alerte objet inconnu (hors allowlist)" || echec "pas d'alerte d'intrusion"
grep -q "\[ALERTE SEUIL\]" <<<"$LOGS_SUP" && ok "alerte de seuil" || echec "pas d'alerte de seuil"

# --------------------------------------------------------------------------
titre "7. Secrets"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1 && git ls-files | grep -Eiq '\.(key|pem|p12|pfx)$'; then
    echec "fichier de clé suivi par Git : $(git ls-files | grep -Ei '\.(key|pem|p12|pfx)$' | tr '\n' ' ')"
else
    ok "aucun fichier de clé suivi par Git"
fi
# Une vraie clé PEM commence en début de ligne ; un motif de recherche cité entre
# guillemets dans un script ne doit pas être pris pour une clé.
TROUVE=$(grep -RIlE --exclude-dir=.git -- '^-----BEGIN [A-Z ]*PRIVATE KEY-----$' . | tr '\n' ' ')
[[ -n "$TROUVE" ]] && echec "clé privée en clair dans : $TROUVE" || ok "aucune clé privée en clair dans les sources"
IMAGE=$($DC images -q superviseur 2>/dev/null | head -1)
if [[ -n "$IMAGE" ]] && $DOCKER run --rm --entrypoint sh "$IMAGE" -c 'find /app -name "*.key" -o -name "*.pem" | grep -q .'; then
    echec "clé présente dans l'image Docker"
else
    ok "aucune clé embarquée dans l'image Docker"
fi
r=$(py_dans temp-salon <<'PYTHON' | tail -1
import os, stat
print(oct(stat.S_IMODE(os.stat('/certs/client.key').st_mode)))
PYTHON
)
[[ "$r" == "0o600" ]] && ok "clé privée d'un capteur en permissions 600" || echec "permissions de la clé : $r"
r=$(py_dans temp-salon <<'PYTHON' | tail -1
import os
print('ca.key' in os.listdir('/certs'))
PYTHON
)
[[ "$r" == "False" ]] && ok "la clé de l'AC n'est pas accessible aux capteurs" || echec "ca.key visible par un capteur"

# --------------------------------------------------------------------------
titre "Résultat"
printf "%d vérifications réussies, %d échecs\n" "$REUSSIS" "$ECHECS"
[[ $ECHECS -eq 0 ]]
