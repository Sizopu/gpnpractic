ARG DOCKER_REGISTRY
ARG PYTHON_BASE_IMAGE

FROM ${DOCKER_REGISTRY}/${PYTHON_BASE_IMAGE}
USER 0

# Объявление переменных
ARG PIP_INDEX_URL_PARAM
ARG PIP_TRUSTED_HOST_PARAM
ARG REDOS_REPO_FILE

# Настройка рабочей директории
ENV APP_ROOT=/opt/app-root/src
WORKDIR $APP_ROOT

# Настройка сертификатов
COPY ./docker/certs /etc/pki/ca-trust/source/anchors
RUN update-ca-trust

# Настройка репозиториев RedOS
RUN mkdir "/etc/yum.repos.d/main"
COPY ./docker/yum.repos.d/${REDOS_REPO_FILE} /etc/yum.repos.d/main/${REDOS_REPO_FILE}
RUN echo "sslverify=False" >> /etc/dnf/dnf.conf && echo "reposdir=/etc/yum.repos.d/main" >> /etc/dnf/dnf.conf
RUN dnf repolist && \
    dnf -y --setopt=tsflags=nodocs update && \
    dnf -y --setopt=tsflags=nodocs install \
    poetry \
    nmap \
    && dnf -y clean all


ENV LC_CTYPE=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    ENV=$APP_ROOT/.venv/bin/activate \
    BASH_ENV=$APP_ROOT/.venv/bin/activate \
    PROMPT_COMMAND="${APP_ROOT}/.venv/bin/activate" \
    PWD=$APP_ROOT \
    HOME=$APP_ROOT \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_INDEX_URL=${PIP_INDEX_URL_PARAM} \
    PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST_PARAM} \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    PYTHONWARNINGS="ignore:Unverified HTTPS request"
# Копирование исходников backend
COPY ./src/QB.Backend ./
# Копирование списка зависимостей
COPY ./docker/config/QB.Backend/pyproject.toml ./

# Копирование enytpoint.sh
COPY --chown=app:0 --chmod=0750 ./docker/bin/QB.Backend/* ${APP_ROOT}/

RUN sed -i -e "s#https://pypi.org/simple#${PIP_INDEX_URL_PARAM}#g" poetry.lock && \
    poetry source add --priority=primary repo ${PIP_INDEX_URL_PARAM} && \
    poetry lock && \
    poetry install --no-root

RUN mkdir $APP_ROOT/static && \
    groupadd --gid 10000 app && useradd --uid 10000 --gid app --shell /bin/bash -d $APP_ROOT app ||true && \
    chown -R app:0 $APP_ROOT && \
    chmod 750 -R $APP_ROOT && \
    chmod 755 -R $APP_ROOT/static

COPY --chown=app:0 --chmod=0644 ./docker/ssl/certs/certificate.crt /opt/app-root/etc/certificate.crt
COPY --chown=app:0 --chmod=0600 ./docker/ssl/certs/private.key /opt/app-root/etc/private.key

# Переключение на non-root пользователя
USER app

# Запуск приложения с использованием Python из виртуального окружения, подготовленного через poetry
ENTRYPOINT ["/opt/app-root/src/docker-entrypoint.sh"]
CMD ["backend"]