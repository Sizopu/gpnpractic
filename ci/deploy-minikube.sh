#!/usr/bin/env bash
set -euo pipefail

: "${MINIKUBE_HOST:?}"
: "${MINIKUBE_USER:?}"
: "${SSH_PRIVATE_KEY:?}"
: "${QB_ENV_FILE:?}"

RELEASE="${RELEASE:-quotation-book}"
NAMESPACE="${NAMESPACE:-demo}"
VALUES_OVERLAY="${VALUES_OVERLAY:-values-minikube.yaml}"
HELM_TIMEOUT="${HELM_TIMEOUT:-25m}"

mkdir -p ~/.ssh
printf "%s" "$SSH_PRIVATE_KEY" > ~/.ssh/id_ed25519
chmod 600 ~/.ssh/id_ed25519
ssh-keyscan -H "$MINIKUBE_HOST" >> ~/.ssh/known_hosts

cp "$QB_ENV_FILE" .env
set -a; . ./.env; set +a

export DOCKER_REGISTRY="${DOCKER_REGISTRY:-quay.io}"
export TLS_ENABLED="${TLS_ENABLED:-true}"
export TLS_CREATE="${TLS_CREATE:-true}"
export TLS_SECRET_NAME="$(echo "${TLS_SECRET_NAME:-quotation-book-tls}" | tr '[:upper:]' '[:lower:]')"

if [ "$TLS_CREATE" = "true" ]; then
  CERT_SRC="./docker/ssl/certs/certificate.crt"
  KEY_SRC="./docker/ssl/certs/private.key"
  CA_SRC="./docker/certs/sandbox_ca_root.crt"

  [ -f "$CERT_SRC" ] || { echo "missing $CERT_SRC"; exit 1; }
  [ -f "$KEY_SRC" ]  || { echo "missing $KEY_SRC"; exit 1; }

  export TLS_CERTIFICATE_CRT_B64="$(cat "$CERT_SRC" | base64 | tr -d '\n')"
  export TLS_PRIVATE_KEY_B64="$(cat "$KEY_SRC" | base64 | tr -d '\n')"
  if [ -f "$CA_SRC" ]; then
    export TLS_CA_ROOT_CRT_B64="$(cat "$CA_SRC" | base64 | tr -d '\n')"
  else
    export TLS_CA_ROOT_CRT_B64=""
  fi
fi

VALUES_TPL="./ci/values-from-env.tpl.yaml"
[ -f "$VALUES_TPL" ] || { echo "missing $VALUES_TPL"; exit 1; }

envsubst < "$VALUES_TPL" > /tmp/values-ci.yaml
cp "$VALUES_OVERLAY" /tmp/values-overlay.yaml

tar -czf /tmp/qb-chart.tgz \
  Chart.yaml templates values.yaml values-prod.yaml values-minikube.yaml ci/values-from-env.tpl.yaml

tar -czf /tmp/qb-bundle.tgz -C /tmp qb-chart.tgz values-ci.yaml values-overlay.yaml

scp -i ~/.ssh/id_ed25519 /tmp/qb-bundle.tgz "$MINIKUBE_USER@$MINIKUBE_HOST:/tmp/qb-bundle.tgz"

ssh -i ~/.ssh/id_ed25519 "$MINIKUBE_USER@$MINIKUBE_HOST" bash -lc "
set -euo pipefail

RELEASE='$RELEASE'
NS='$NAMESPACE'
HELM_TIMEOUT='$HELM_TIMEOUT'

mkdir -p /tmp/qb
tar -xzf /tmp/qb-bundle.tgz -C /tmp/qb

CHART=/tmp/qb/qb-chart.tgz
V1=/tmp/qb/values-ci.yaml
V2=/tmp/qb/values-overlay.yaml

kubectl get ns \"\$NS\" >/dev/null 2>&1 || kubectl create ns \"\$NS\"

if ! command -v helm >/dev/null 2>&1; then
  curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

h() {
  helm upgrade --install \"\$RELEASE\" \"\$CHART\" -n \"\$NS\" --create-namespace \
    -f \"\$V1\" -f \"\$V2\" \$1 --wait --timeout \"\$HELM_TIMEOUT\"
}

BASE='--set postgres.enabled=true --set redis.enabled=true --set rabbitmq.enabled=true'
h \"\$BASE\"

h \"\$BASE --set postgresMigration.enabled=true\"

BASE_MINIO=\"\$BASE --set minio.enabled=true\"
h \"\$BASE_MINIO\"

h \"\$BASE_MINIO --set minioMigration.enabled=true\"

BASE_KC=\"\$BASE_MINIO --set keycloak.enabled=true\"
h \"\$BASE_KC\"

BASE_BE=\"\$BASE_KC --set backend.enabled=true\"
h \"\$BASE_BE\"

BASE_FE=\"\$BASE_BE --set frontend.enabled=true\"
h \"\$BASE_FE\"

h \"\$BASE_FE --set postgresMigration.enabled=false --set minioMigration.enabled=false\"

kubectl -n \"\$NS\" get pods,svc -o wide
helm -n \"\$NS\" status \"\$RELEASE\"
"
