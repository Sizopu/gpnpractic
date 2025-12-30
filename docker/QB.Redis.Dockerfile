ARG DOCKER_REGISTRY
ARG REDIS_BASE_IMAGE

FROM ${DOCKER_REGISTRY}/${REDIS_BASE_IMAGE}
USER 0

COPY --chown=gpn:0 --chmod=0644 ./docker/certs /etc/pki/ca-trust/source/anchors
RUN groupadd --gid 10000 gpn && useradd --uid 10000 --gid 10000 --shell /bin/bash gpn && \
    mkdir -p /opt/redis/{certs,conf} && \
    chown -R gpn:0 /opt/redis/{certs,conf} && \
    chown -R gpn:0 /etc/redis && \
    mkdir -p /var/lib/redis && \
    chown -R gpn:0 /var/lib/redis && \
    update-ca-trust

COPY --chmod=0755 --chown=0:0 ./docker/bin/QB.Redis/docker-entrypoint.sh /entrypoint.sh

COPY --chown=gpn:0 --chmod=0644 ./docker/ssl/certs/certificate.crt /opt/redis/certs
COPY --chown=gpn:0 --chmod=0600 ./docker/ssl/certs/private.key /opt/redis/certs

USER gpn
EXPOSE 6380