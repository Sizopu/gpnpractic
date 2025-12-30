ARG DOCKER_REGISTRY
ARG NODE_BASE_IMAGE

FROM ${DOCKER_REGISTRY}/${NODE_BASE_IMAGE} AS builder
ARG NPM_REGISTRY

USER 0
WORKDIR /opt/app-root/src
COPY ./docker/certs /etc/pki/ca-trust/source/anchors
COPY ./src/QB.Javascript.Obs/package*.json ./
RUN update-ca-trust && \
    npm install --registry=${NPM_REGISTRY}

COPY ./src/QB.Javascript.Obs/ .

RUN chown -R 10000:0 /opt/app-root/src && \
    chmod -R 755 /opt/app-root/src

# Runtime
FROM ${DOCKER_REGISTRY}/${NODE_BASE_IMAGE}

USER 0
RUN groupadd -g 10000 app && \
    useradd -u 10000 -g 10000 app && \
    mkdir /opt/app-root/certs

WORKDIR /opt/app-root

COPY --chown=10000:0 --chmod=0644 ./docker/ssl/certs/certificate.crt /opt/app-root/certs/
COPY --chown=10000:0 --chmod=0600 ./docker/ssl/certs/private.key /opt/app-root/certs/
# Подготовка корневых сертфикатов
COPY --chown=10000:0 --chmod=0644 ./docker/certs /etc/pki/ca-trust/source/anchors
COPY --chown=10000:0 --chmod=0644 ./docker/certs/sandbox_ca_root.crt /opt/app-root/certs/
RUN update-ca-trust

COPY --from=builder --chown=10000:0 --chmod=0755 /opt/app-root/src /opt/app-root/app

USER 10000

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f https://localhost:3000/ || exit 1

ENTRYPOINT ["node", "/opt/app-root/app/server.js"]