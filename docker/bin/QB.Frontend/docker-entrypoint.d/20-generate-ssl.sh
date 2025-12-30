#!/bin/sh

set -e

# Проверка наличия значения в переменной CERT_FQDN
if [ -z "${CERT_FQDN}" ]; then
    # echo "Переменная CERT_FQDN не задана. Этап создания самоподписанного сертификата пропущен" >&2
    exit 0
fi


cd /etc/nginx/ssl/
envsubst < /opt/app-root/templates/crt.conf.template > crt.conf
openssl req -x509 -nodes -days 1024 -newkey rsa:2048 -config crt.conf -keyout nginx-private.key -out nginx-chain.pem

# openssl genrsa -out /etc/nginx/ssl/nginx-private.key 2048
openssl dhparam -out dhparam.pem 2048

chmod 400 dhparam.pem
chmod 400 nginx-private.key
cd -