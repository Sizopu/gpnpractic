#!/bin/bash
mkdir -p /etc/redis

echo "dir /var/lib/redis" > $REDIS_CONF

if [[ -z ${REDIS_PASS+x} ]]; then
    echo 'ERROR: Пароль для Redis не задан. Он обязателен по требованиям ИБ (параметр $REDIS_PASS)'
    exit 1
else
    if [[ -z ${REDIS_PORT+x} ]]; then
        REDIS_PORT=6379
    fi
    echo -e "requirepass $REDIS_PASS\nport $REDIS_PORT" >> $REDIS_CONF
fi

if [[ -n ${ENABLE_SSL+x} ]]; then
    if [[ ! (-z ${TLS_PORT+x} || -z ${TLS_CERT_FILE+x} || -z ${TLS_CA_CERT_FILE+x} || -z ${TLS_KEY_FILE+x}) ]]; then
        if [[ -f ${TLS_CERT_FILE} && -f ${TLS_CA_CERT_FILE} && -f ${TLS_KEY_FILE} ]]; then
            cat <<-EOF >> $REDIS_CONF
tls-port ${TLS_PORT}
tls-cert-file ${TLS_CERT_FILE}
tls-ca-cert-file ${TLS_CA_CERT_FILE}
tls-key-file ${TLS_KEY_FILE}
tls-protocols 'TLSv1.2 TLSv1.3'
EOF
            case "${TLS_CLIENT_CERT_AUTH,,}" in
                true)
                    echo "tls-auth-clients yes" >> $REDIS_CONF
                    ;;
                false)
                    echo "tls-auth-clients no" >> $REDIS_CONF
                    ;;
                *)
                    echo "tls-auth-clients no" >> $REDIS_CONF
                    ;;
            esac
        else
            cat <<EOF
ERROR: One or more SSL files are missing.
Check environments with paths for certificates.
CA_CERT_FILE: ${TLS_CA_CERT_FILE}
KEY_FILE: ${TLS_KEY_FILE}
CERT_FILE: ${TLS_CERT_FILE}
EOF
            exit 1
        fi
        if [[ -n ${TLS_KEY_FILE_PASS+x} ]]; then
            echo "tls-key-file-pass $TLS_KEY_FILE_PASS" >> $REDIS_CONF
        fi
    else
        echo "ERROR: SSL parameters are not set correctly (env: TLS_PORT, TLS_CERT_FILE, TLS_CA_CERT_FILE, TLS_KEY_FILE)"
        exit 1
    fi
fi
exec "$@"