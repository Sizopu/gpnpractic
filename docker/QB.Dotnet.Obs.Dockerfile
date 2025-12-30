ARG DOCKER_REGISTRY
ARG DOTNET_BASE_IMAGE
ARG DOTNET_RUNTIME_IMAGE

# Build
FROM ${DOCKER_REGISTRY}/${DOTNET_BASE_IMAGE} AS build
WORKDIR /opt/app-root
COPY ./src/QB.Dotnet.Obs/ .
RUN dotnet restore
RUN dotnet publish -c Release -o out

# Runtime
FROM ${DOCKER_REGISTRY}/${DOTNET_RUNTIME_IMAGE}
USER 0
# Создаём non-root пользователя
RUN groupadd -g 10000 app && \
    useradd -u 10000 -g 10000 app && \
    mkdir /opt/app-root/{out,certs} && \
    chown -R 10000:0 /opt/app-root/{out,certs}

WORKDIR /opt/app-root

# Копируем серверный сертификат
COPY --chown=10000:0 --chmod=0644 ./docker/ssl/certs/cert.pfx /opt/app-root/certs/

# Подготовавливаем корневые сертификаты
COPY ./docker/certs /etc/pki/ca-trust/source/anchors
RUN update-ca-trust

# Копируем бинарный файл с build stage
COPY --from=build --chown=10000:0 /opt/app-root/out .

EXPOSE 1443

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -k -f https://localhost:1443/health || exit 1

USER 10000

ENTRYPOINT ["dotnet", "HealthService.dll"]