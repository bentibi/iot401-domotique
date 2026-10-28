"""Création locale des certificats, au démarrage de Docker Compose.

Les clés ne sont jamais écrites dans le dossier Git : elles restent
uniquement dans les volumes privés Docker.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

DOSSIER_CA = Path('/volumes/autorite')
APPAREILS = [
    'presence-entree', 'temp-salon', 'temp-chambre', 'temp-cuisine',
    'superviseur', 'capteur-test',
]


def sauver(path, donnees, mode=0o600, utilisateur=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(donnees)
    os.chmod(path, mode)
    if utilisateur is not None:
        os.chown(path, utilisateur, utilisateur)


def cle_en_pem(cle):
    return cle.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                             serialization.NoEncryption())


def certificat_pem(certificat):
    return certificat.public_bytes(serialization.Encoding.PEM)


def generer_autorite():
    cle_fichier = DOSSIER_CA / 'ca.key'
    cert_fichier = DOSSIER_CA / 'ca.crt'
    if cle_fichier.exists() and cert_fichier.exists():
        cle = serialization.load_pem_private_key(cle_fichier.read_bytes(), password=None)
        certificat = x509.load_pem_x509_certificate(cert_fichier.read_bytes())
        return cle, certificat

    cle = ec.generate_private_key(ec.SECP256R1())
    nom = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'IOT401 Maison CA')])
    maintenant = datetime.now(timezone.utc)
    certificat = (
        x509.CertificateBuilder()
        .subject_name(nom).issuer_name(nom).public_key(cle.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(maintenant - timedelta(days=1))
        .not_valid_after(maintenant + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(x509.KeyUsage(digital_signature=True, content_commitment=False,
                       key_encipherment=False, data_encipherment=False,
                       key_agreement=False, key_cert_sign=True, crl_sign=True,
                       encipher_only=False, decipher_only=False), critical=True)
        .sign(cle, hashes.SHA256())
    )
    sauver(cle_fichier, cle_en_pem(cle))
    sauver(cert_fichier, certificat_pem(certificat), 0o644)
    return cle, certificat


def generer_identite(nom, cle_ca, cert_ca, serveur=False):
    dossier = Path('/volumes') / nom
    cle_fichier = dossier / ('server.key' if serveur else 'client.key')
    crt_fichier = dossier / ('server.crt' if serveur else 'client.crt')
    ca_fichier = dossier / 'ca.crt'
    sauver(ca_fichier, certificat_pem(cert_ca), 0o644)

    if cle_fichier.exists() and crt_fichier.exists():
        return
    cle = ec.generate_private_key(ec.SECP256R1())
    maintenant = datetime.now(timezone.utc)
    certificat = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, nom)]))
        .issuer_name(cert_ca.subject)
        .public_key(cle.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(maintenant - timedelta(days=1))
        .not_valid_after(maintenant + timedelta(days=90))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.ExtendedKeyUsage([
            ExtendedKeyUsageOID.SERVER_AUTH if serveur else ExtendedKeyUsageOID.CLIENT_AUTH
        ]), critical=False)
        .add_extension(x509.SubjectAlternativeName([x509.DNSName('broker')]), critical=False)
        .sign(cle_ca, hashes.SHA256())
    )
    # Dans l'image Mosquitto, le service fonctionne avec l'UID/GID 1883.
    # Seul ce service a besoin de pouvoir lire sa clé serveur.
    proprietaire = 1883 if serveur else None
    sauver(cle_fichier, cle_en_pem(cle), 0o600, proprietaire)
    sauver(crt_fichier, certificat_pem(certificat), 0o644)


def main():
    DOSSIER_CA.mkdir(parents=True, exist_ok=True)
    cle_ca, cert_ca = generer_autorite()
    generer_identite('broker', cle_ca, cert_ca, serveur=True)
    for appareil in APPAREILS:
        generer_identite(appareil, cle_ca, cert_ca)
    print('PKI prête : 4 capteurs, 1 superviseur, 1 test et 1 broker.')
    print('Clés privées conservées dans les volumes Docker, non exportées.')


if __name__ == '__main__':
    main()
