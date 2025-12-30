
ARG DOCKER_REGISTRY
ARG MAVEN_BASE_IMAGE
ARG JDK_BASE_IMAGE


FROM ${DOCKER_REGISTRY}/${MAVEN_BASE_IMAGE} AS builder
USER 0
WORKDIR /opt/app-root/src
ARG MAVEN_REPO_PARAM

COPY ./src/QB.Java.Obs/pom.xml .
COPY ./src/QB.Java.Obs/src/main/java/ ./src/main/java/
COPY ./docker/config/QB.Java.Obs/settings.xml /usr/share/maven/conf/settings.xml

# Настройка сертификатов
COPY ./docker/certs /etc/pki/ca-trust/source/anchors

RUN update-ca-trust && \
    sed -i -e "s#https://proxy.repos.devzone.local/repository/maven2-all#${MAVEN_REPO_PARAM}#g" /usr/share/maven/conf/settings.xml && \
    mvn clean package -DskipTests && \
    chown -R 1001:0 /opt/app-root/src/target && \
    chmod -R 755 /opt/app-root/src/target


FROM ${DOCKER_REGISTRY}/${JDK_BASE_IMAGE}
USER 0
RUN groupadd -g 10000 app && \
    useradd -u 10000 -g 10000 app

WORKDIR /opt/app-root

RUN mkdir -p /opt/app-root/{bin,certs}
COPY --from=builder --chown=10000:0 --chmod=0750 /opt/app-root/src/target/metrics-app-1.0.jar /opt/app-root/bin/metrics-app.jar
COPY --chown=10000:0 --chmod=0600 ./docker/ssl/certs/keystore.p12 /opt/app-root/certs/

# Подготовка корневых сертификатов
COPY ./docker/certs /etc/pki/ca-trust/source/anchors
RUN update-ca-trust

EXPOSE 8443

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -k https://localhost:8443/metrics || exit 1

USER 10000

ENTRYPOINT ["java", "-jar", "/opt/app-root/bin/metrics-app.jar"]