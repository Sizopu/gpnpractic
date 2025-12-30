ARG DOCKER_REGISTRY
ARG DB_MIGRATION_BASE_IMAGE
ARG POSTGRES_DB_CONNECTION_ENCRYPT

FROM ${DOCKER_REGISTRY}/${DB_MIGRATION_BASE_IMAGE}
LABEL maintainer="GpnDs"
USER root
COPY ./docker/certs /etc/pki/ca-trust/source/anchors
RUN update-ca-trust
COPY --chmod=0750 --chown=1000:0 ./docker/config/QB.Postgres.Migration/*.sql /migrations/
COPY --chmod=0750 --chown=1000:0 ./docker/bin/QB.Postgres.Migration/docker-entrypoint.sh /docker-entrypoint.sh

USER 1000

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD [ "/opt/app-root/src/migrate.sh" ]
