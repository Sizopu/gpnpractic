ARG DOCKER_REGISTRY=quay.io/dev_zone
ARG KEYCLOAK_BASE_IMAGE=redos/ubi7/keycloak-23:latest

FROM ${DOCKER_REGISTRY}/${KEYCLOAK_BASE_IMAGE}

USER root

COPY ./docker/certs /etc/pki/ca-trust/source/anchors
RUN update-ca-trust && \
    mkdir -p /usr/share/java/keycloak/status && \
    chown -R keycloak:0 /usr/share/java/keycloak/status

WORKDIR /usr/share/java/keycloak

COPY --chown=keycloak:0 --chmod=0644 \
  ./docker/config/QB.Keycloak/realm-export.json \
  /usr/share/java/keycloak/realm-export.json

# === ВАЖНО: добавляем TLS-файлы внутрь образа (то, чего у тебя сейчас нет) ===
COPY --chown=keycloak:keycloak --chmod=0644 \
  ./docker/ssl/certs/certificate.crt \
  /usr/share/java/keycloak/conf/certificate.crt

COPY --chown=keycloak:keycloak --chmod=0600 \
  ./docker/ssl/certs/private.key \
  /usr/share/java/keycloak/conf/private.key

COPY --chown=keycloak:0 --chmod=0750 \
  ./docker/bin/QB.Keycloak/docker-entrypoint.sh \
  /usr/share/java/keycloak/bin/docker-entrypoint.sh

# Чтобы не видеть "build time non-cli properties ... ignored during run time"
ENV KC_DB=postgres
ENV KC_HEALTH_ENABLED=true
ENV KC_METRICS_ENABLED=true

EXPOSE 1443

USER keycloak
RUN /usr/share/java/keycloak/bin/kc.sh build

ENTRYPOINT ["/usr/share/java/keycloak/bin/docker-entrypoint.sh"]
