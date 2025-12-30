ARG DOCKER_REGISTRY
ARG MINIO_BASE_IMAGE_CLIENT

FROM $DOCKER_REGISTRY/$MINIO_BASE_IMAGE_CLIENT

USER 0
RUN groupadd --gid 10000 gpn && useradd --uid 10000 --gid 10000 --shell /bin/bash gpn && \
    mkdir -p /.mc && \
    chown -R gpn:0 /.mc

COPY --chown=gpn:0 --chmod=0644 ./docker/certs  /etc/ssl/certs
COPY --chown=gpn:0 --chmod=0750 ./docker/bin/QB.Minio.Migration/docker-entrypoint.sh /opt/bitnami/minio-client/docker-entrypoint.sh

USER gpn

ENTRYPOINT ["/opt/bitnami/minio-client/docker-entrypoint.sh"]