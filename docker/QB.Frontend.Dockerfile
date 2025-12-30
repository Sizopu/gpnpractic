ARG DOCKER_REGISTRY
ARG NGINX_BASE_IMAGE=dev_zone/redos/ubi8/nginx:1.2.6.15-dev

FROM ${DOCKER_REGISTRY}/${NGINX_BASE_IMAGE}
ENV APP_ROOT=/opt/app-root
WORKDIR $APP_ROOT
USER 0

#  Подготовка корневых сертификатов
COPY ./docker/certs /etc/pki/ca-trust/source/anchors

# Подготовка необходимых директорий
RUN rm -rf /etc/nginx/conf.d/* && \
    rm -rf /${APP_ROOT}/etc/nginx.d/* && \
    mkdir -p ${APP_ROOT}/etc/nginx.d/{http,server,location} && \
    mkdir -p ${APP_ROOT}/src/static && \
    update-ca-trust

### HTTP: ###
# Основной файл конфигурации nginx
COPY --chown=0:0 --chmod=0644 ./docker/config/QB.Frontend/base-nginx.conf /etc/nginx/nginx.conf

# Заголовки уровня http установленные по требованиям КТ-233, которые не будут меняться # HTTP - base-http-headers.conf
# Добавление лимитов по требованиям ИБ. Лимиты могут быть разными для проектов, при необходимости файл можно переписать поверх - common-server-limits.conf
COPY --chown=0:0 --chmod=0644 ./docker/config/QB.Frontend/templates/http/*  ${APP_ROOT}/etc/nginx.d/http


### SERVER: ###
#Типовая конфигурация сервера c поддержкой TLS/SSL
COPY --chown=default:0 --chmod=0644 ./docker/config/QB.Frontend/default-ssl-server.conf ${APP_ROOT}/etc/nginx.d/default-ssl-server.conf

# Заголовки уровня server установленные по требованиям КТ-233, которые могут меняться по согласованию.
# При необходимости можно определить путь /opt/app-root/etc/nginx.d как volume и заменить файлы по-умолчанию
COPY --chown=default:0 --chmod=0644 ./docker/config/QB.Frontend/templates/server/base-server-headers.conf ${APP_ROOT}/etc/nginx.d/server/common-server-headers.conf

# Добавление location /health и location ~ /\. { deny all; return 404; }
COPY --chown=default:0 --chmod=0644 ./docker/config/QB.Frontend/templates/server/common-server-inc.conf ${APP_ROOT}/etc/nginx.d/server/common-server-inc.conf

# Заголовки для сервера c поддержкой TLS/SSL по требованиям ИБ
COPY --chown=default:0 --chmod=0644 ./docker/config/QB.Frontend/templates/server/common-server-ssl-headers.conf ${APP_ROOT}/etc/nginx.d/server/common-server-ssl-headers.conf


### LOCATION: ###
# Заголовки уровня location
COPY --chown=default:0 --chmod=0644 ./docker/config/QB.Frontend/templates/location/common-location-headers.conf ${APP_ROOT}/etc/nginx.d/location/common-location-headers.conf
# Доавбление шаблона с секция location проекта
COPY --chown=default:0 --chmod=0644 ./docker/config/QB.Frontend/default-location-conf.template ${APP_ROOT}/etc/nginx/templates/default-location-conf.template

# Entrypoints
COPY --chown=0:0 --chmod=0755 ./docker/bin/QB.Frontend/* ${APP_ROOT}/

# Добавление самодписанных сертификатов (только для dev). Либо задайте переменную CERT_FQDN=<FQDN> \
# в окружения контейнера для автоматической генерации сертификатов сервера через docker-entrypoint.d
COPY --chown=default:0 --chmod=0644 ./docker/ssl/certs/certificate.crt /etc/nginx/ssl/nginx-chain.pem
COPY --chown=default:0 --chmod=0600 ./docker/ssl/certs/private.key /etc/nginx/ssl/nginx-private.key
COPY --chown=default:0 --chmod=0600 ./docker/ssl/certs/dhparam.pem /etc/nginx/ssl/dhparam.pem

EXPOSE 8443
# Переключение на non-root пользователя
USER default

# Установка entrypoint по умолчанию
ENTRYPOINT ["/opt/app-root/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]