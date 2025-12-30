ARG DOCKER_REGISTRY
ARG MINIO_BASE_IMAGE

FROM $DOCKER_REGISTRY/$MINIO_BASE_IMAGE
USER 0
RUN groupadd --gid 10000 gpn && useradd --uid 10000 --gid 10000 --shell /bin/bash gpn && \
    mkdir -p /certs && \
    mkdir -p /opt/bitnami/minio /bitnami/minio/data /.mc/certs && \
    chown -R gpn:0 /certs && \
    chown -R gpn:0 /opt/bitnami/minio && \
    chown -R gpn:0 /bitnami/minio/data && \
    chown -R gpn:0 /.mc

COPY --chown=gpn:0 --chmod=0644 ./docker/certs  /etc/ssl/certs
COPY --chown=gpn:0 --chmod=0644 ./docker/ssl/certs/certificate.crt /certs/public.crt
COPY --chown=gpn:0 --chmod=0600 ./docker/ssl/certs/private.key /certs/private.key

USER gpn