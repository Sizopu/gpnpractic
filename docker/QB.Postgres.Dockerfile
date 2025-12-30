ARG DOCKER_REGISTRY
ARG POSTGRES_BASE_IMAGE

FROM ${DOCKER_REGISTRY}/${POSTGRES_BASE_IMAGE}

USER 0

# Создаем пользователя и группы
RUN groupadd --gid 10000 gpn && \
    useradd --uid 10000 --gid 10000 --shell /bin/bash gpn && \
    mkdir -p /opt/postgres/certs && \
    mkdir -p /var/lib/postgresql/data/pgdata && \
    mkdir -p /var/run/postgresql && \
    chown -R gpn:gpn /var/lib/postgresql/data/pgdata && \
    chown -R gpn:gpn /var/run/postgresql && \
    chmod 755 /var/run/postgresql

# Создаем директорию для SSL
RUN mkdir -p /tmp/pgssl && \
    chown -R gpn:gpn /tmp/pgssl && \
    chmod 700 /tmp/pgssl

# Копируем SSL файлы как root
COPY --chown=0:0 ./docker/ssl/certs/certificate.crt /opt/postgres/certs/certificate.crt
COPY --chown=0:0 ./docker/ssl/certs/private.key /opt/postgres/certs/private.key

# Создаем скрипт инициализации с SSL
RUN echo '#!/bin/bash' > /init-with-ssl.sh && \
    echo 'set -e' >> /init-with-ssl.sh && \
    echo '' >> /init-with-ssl.sh && \
    echo '# Копируем SSL файлы с правильными правами' >> /init-with-ssl.sh && \
    echo 'if [ -f /opt/postgres/certs/private.key ] && [ -f /opt/postgres/certs/certificate.crt ]; then' >> /init-with-ssl.sh && \
    echo '    echo "Setting up SSL..."' >> /init-with-ssl.sh && \
    echo '    cp /opt/postgres/certs/certificate.crt /tmp/pgssl/server.crt' >> /init-with-ssl.sh && \
    echo '    cp /opt/postgres/certs/private.key /tmp/pgssl/server.key' >> /init-with-ssl.sh && \
    echo '    chown gpn:gpn /tmp/pgssl/server.crt /tmp/pgssl/server.key' >> /init-with-ssl.sh && \
    echo '    chmod 644 /tmp/pgssl/server.crt' >> /init-with-ssl.sh && \
    echo '    chmod 600 /tmp/pgssl/server.key' >> /init-with-ssl.sh && \
    echo '    echo "SSL certificates ready"' >> /init-with-ssl.sh && \
    echo 'fi' >> /init-with-ssl.sh && \
    echo '' >> /init-with-ssl.sh && \
    echo '# Выполняем стандартную инициализацию PostgreSQL' >> /init-with-ssl.sh && \
    echo '/usr/local/bin/docker-entrypoint.sh postgres "$@"' >> /init-with-ssl.sh && \
    chmod +x /init-with-ssl.sh

# Копируем entrypoint скрипт для создания пользователей и баз данных
COPY --chmod=755 --chown=0:0 ./docker/bin/QB.Postgres/docker-entrypoint.sh /docker-entrypoint-initdb.d/

USER gpn

# Используем стандартный entrypoint