# On garde l'image officielle Mosquitto, mais on y ajoute notre configuration.
FROM eclipse-mosquitto:2.0.22

COPY mosquitto/mosquitto.conf /mosquitto/config/mosquitto.conf
COPY mosquitto/acl.conf /mosquitto/config/acl.conf

# Seul le compte du broker doit pouvoir lire les ACL.
RUN chown 1883:1883 /mosquitto/config/*.conf \
    && chmod 644 /mosquitto/config/mosquitto.conf \
    && chmod 600 /mosquitto/config/acl.conf

USER 1883:1883
