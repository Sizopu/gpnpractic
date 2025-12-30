#!/bin/sh
set -e

# Функция для логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# Настройка alias для MinIO с игнорированием SSL (для тестирования)
setup_minio_alias() {
    log "Setting up MinIO alias..."
    
    # Формируем полный URL
    local MINIO_FULL_URL="${MINIO_SCHEME}://${MINIO_HOST}:${MINIO_PORT}"
    log "Using MinIO URL: ${MINIO_FULL_URL}"
    
    # Пробуем с SSL, если не получается - пробуем без SSL
    if ! mc alias set quotation-book-minio "${MINIO_FULL_URL}" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}" --insecure; then
        log "SSL connection failed, trying without SSL..."
        local MINIO_FULL_URL_HTTP="http://${MINIO_HOST}:${MINIO_PORT}"
        mc alias set quotation-book-minio "${MINIO_FULL_URL_HTTP}" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}"
    fi
    
    log "MinIO alias configured successfully"
}

# Ожидание готовности MinIO сервера
wait_for_minio() {
    log "Waiting for MinIO server to be ready..."
    local retries=30
    local wait_time=5

    # Проверяем готовность сервера
    until mc ready quotation-book-minio --insecure >/dev/null 2>&1 || [ $retries -eq 0 ]; do
        log "Waiting for MinIO server... ($retries retries left)"
        sleep $wait_time
        retries=$((retries - 1))
    done

    if [ $retries -eq 0 ]; then
        log "WARNING: MinIO server 'quotation-book-minio' is not ready after $((30 * $wait_time)) seconds"
        log "Continuing anyway..."
    else
        log "MinIO server is ready!"
    fi
}

# Создание бакета
create_buckets() {
    log "Creating required buckets..."
    
    # Создаем бакет с опцией --insecure если нужно
    if ! mc mb quotation-book-minio/${MINIO_BUCKET_NAME} --insecure; then
        log "Trying without --insecure option..."
        mc mb quotation-book-minio/${MINIO_BUCKET_NAME} || true
    fi
    
    log "Bucket ${MINIO_BUCKET_NAME} created or already exists"
}

# Основной процесс
main() {
    log "Starting MinIO client setup..."

    setup_minio_alias
    wait_for_minio
    create_buckets

    log "MinIO client setup with bucket completed successfully"

    # Если переданы дополнительные аргументы, то выполняем их
    if [ $# -gt 0 ]; then
        log "Executing additional commands: $*"
        exec "$@"
    else
        log "No additional commands provided, exiting..."
    fi
}

main "$@"