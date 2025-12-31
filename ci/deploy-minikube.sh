#!/usr/bin/env bash
set -euo pipefail

# --- User-tunable (can be overridden by CI variables) ---
NAMESPACE="${NAMESPACE:-demo}"
RELEASE="${RELEASE:-quotation-book}"
REMOTE_DIR="${REMOTE_DIR:-/tmp/qb}"
VALUES_OVERLAY="${VALUES_OVERLAY:-values-minikube.yaml}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-180s}"

MINIKUBE_HOST="${MINIKUBE_HOST:?MINIKUBE_HOST is required}"
MINIKUBE_USER="${MINIKUBE_USER:?MINIKUBE_USER is required}"

apk add --no-cache bash openssh-client curl tar coreutils gettext >/dev/null

mkdir -p ~/.ssh

write_ssh_key() {
  # Supports both "masked variable" (content) and "file variable" (path).
  if [ -n "${SSH_PRIVATE_KEY:-}" ] && [ -f "${SSH_PRIVATE_KEY:-}" ]; then
    cp "${SSH_PRIVATE_KEY}" ~/.ssh/id_ed25519
  else
    # 1) Try as base64 (common when storing keys safely), 2) fallback to raw.
    if printf '%s' "${SSH_PRIVATE_KEY:-}" | tr -d '\r\n' | base64 -d >/root/.ssh/id_ed25519 2>/dev/null && \
      grep -q "BEGIN" /root/.ssh/id_ed25519; then
      :
    else
      printf '%s\n' "${SSH_PRIVATE_KEY:-}" | tr -d '\r' > ~/.ssh/id_ed25519
    fi
  fi
  chmod 600 ~/.ssh/id_ed25519
}

write_ssh_key

ssh-keyscan -H "$MINIKUBE_HOST" >> ~/.ssh/known_hosts 2>/dev/null

# QB_ENV_FILE is expected to be a GitLab "file" variable.
if [ -n "${QB_ENV_FILE:-}" ] && [ -f "${QB_ENV_FILE:-}" ]; then
  cp "$QB_ENV_FILE" .env
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

export DOCKER_REGISTRY="${DOCKER_REGISTRY:-quay.io}"
export TLS_ENABLED="${TLS_ENABLED:-true}"
export TLS_CREATE="${TLS_CREATE:-true}"
export TLS_SECRET_NAME="$(echo "${TLS_SECRET_NAME:-quotation-book-tls}" | tr '[:upper:]' '[:lower:]')"

if [ "$TLS_CREATE" = "true" ]; then
  CERT_SRC="./docker/ssl/certs/certificate.crt"
  KEY_SRC="./docker/ssl/certs/private.key"
  CA_SRC="./docker/certs/sandbox_ca_root.crt"

  [ -f "$CERT_SRC" ] || { echo "Missing $CERT_SRC"; exit 1; }
  [ -f "$KEY_SRC" ]  || { echo "Missing $KEY_SRC"; exit 1; }

  export TLS_CERTIFICATE_CRT_B64="$(base64 -w0 < "$CERT_SRC")"
  export TLS_PRIVATE_KEY_B64="$(base64 -w0 < "$KEY_SRC")"
  if [ -f "$CA_SRC" ]; then
    export TLS_CA_ROOT_CRT_B64="$(base64 -w0 < "$CA_SRC")"
  else
    export TLS_CA_ROOT_CRT_B64=""
  fi
fi

# Render CI values (envsubst-friendly template).
VALUES_TPL="ci/values-from-env.tpl.yaml"
[ -f "$VALUES_TPL" ] || { echo "Missing $VALUES_TPL"; exit 1; }
envsubst < "$VALUES_TPL" > /tmp/values-ci.yaml

# Package the chart into a Helm-friendly tgz (must contain a top-level directory).
CHART_TGZ=/tmp/qb-chart.tgz
tar -czf "$CHART_TGZ" \
  --transform 's,^,quotation-book/,' \
  Chart.yaml \
  templates \
  values.yaml \
  values-prod.yaml \
  values-minikube.yaml

scp_opts=(
  -i ~/.ssh/id_ed25519
  -o BatchMode=yes
  -o ConnectTimeout=10
)
ssh_opts=(
  -i ~/.ssh/id_ed25519
  -o BatchMode=yes
  -o ConnectTimeout=10
)

remote="$MINIKUBE_USER@$MINIKUBE_HOST"

scp "${scp_opts[@]}" "$CHART_TGZ" "$remote:/tmp/qb-chart.tgz"
scp "${scp_opts[@]}" /tmp/values-ci.yaml "$remote:/tmp/values-ci.yaml"

ssh "${ssh_opts[@]}" "$remote" env \
  NAMESPACE="$NAMESPACE" \
  RELEASE="$RELEASE" \
  REMOTE_DIR="$REMOTE_DIR" \
  VALUES_OVERLAY="$VALUES_OVERLAY" \
  WAIT_TIMEOUT="$WAIT_TIMEOUT" \
  bash -se <<'REMOTE'
set -euo pipefail

ns="${NAMESPACE}"
release="${RELEASE}"
rdir="${REMOTE_DIR}"
overlay="${VALUES_OVERLAY}"
wait_t="${WAIT_TIMEOUT}"

echo "[remote] kubectl: $(command -v kubectl || echo missing)"
kubectl get nodes -o wide

kubectl get ns "$ns" >/dev/null 2>&1 || kubectl create ns "$ns"

if ! command -v helm >/dev/null 2>&1; then
  echo "[remote] helm not found, installing..."
  tmpd="$(mktemp -d)"
  curl -fsSL https://get.helm.sh/helm-v3.16.4-linux-amd64.tar.gz | tar -xz -C "$tmpd"
  sudo mv "$tmpd/linux-amd64/helm" /usr/local/bin/helm || mv "$tmpd/linux-amd64/helm" ~/helm && export PATH="$HOME:$PATH"
fi

rm -rf "$rdir"
mkdir -p "$rdir"
tar -xzf /tmp/qb-chart.tgz -C "$rdir"
chart="$rdir/quotation-book"
[ -f "$chart/Chart.yaml" ] || { echo "[remote] Chart.yaml not found"; ls -la "$rdir"; exit 1; }

[ -f "$chart/$overlay" ] || { echo "[remote] overlay not found in chart: $overlay"; ls -la "$chart"; exit 1; }

wait_pods() {
  local selector="$1"
  echo "[remote] waiting pods Ready: $selector (timeout=$wait_t)"
  kubectl -n "$ns" wait --for=condition=Ready pod -l "$selector" --timeout="$wait_t" || {
    echo "[remote] wait failed for selector: $selector" >&2
    kubectl -n "$ns" get pods -o wide
    exit 1
  }
}

wait_job_complete() {
  local job="$1"
  echo "[remote] waiting job Complete: $job (timeout=$wait_t)"
  kubectl -n "$ns" wait --for=condition=complete "job/$job" --timeout="$wait_t" || {
    echo "[remote] job did not complete: $job" >&2
    kubectl -n "$ns" get jobs -o wide
    kubectl -n "$ns" describe "job/$job" || true
    exit 1
  }
}

helm_up() {
  # Fast helm upgrade/install (no --wait). We wait explicitly with kubectl.
  helm upgrade --install "$release" "$chart" \
    -n "$ns" \
    -f /tmp/values-ci.yaml \
    -f "$chart/$overlay" \
    --history-max 3 \
    "$@"
}

echo "[remote] Stage 1/4: infra (postgres/redis/rabbitmq/minio)"
helm_up \
  --set postgres.enabled=true \
  --set redis.enabled=true \
  --set rabbitmq.enabled=true \
  --set minio.enabled=true \
  --set postgresMigration.enabled=false \
  --set minioMigration.enabled=false \
  --set keycloak.enabled=false \
  --set pgadmin.enabled=false \
  --set backend.enabled=false \
  --set frontend.enabled=false \
  --set observability.dotnet.enabled=false \
  --set observability.java.enabled=false \
  --set observability.javascript.enabled=false

wait_pods "app.kubernetes.io/instance=$release,app.kubernetes.io/name=postgres"
wait_pods "app.kubernetes.io/instance=$release,app.kubernetes.io/name=redis"
wait_pods "app.kubernetes.io/instance=$release,app.kubernetes.io/name=rabbitmq"
wait_pods "app.kubernetes.io/instance=$release,app.kubernetes.io/name=minio"

echo "[remote] Stage 2/4: migrations"
helm_up \
  --set postgres.enabled=true \
  --set redis.enabled=true \
  --set rabbitmq.enabled=true \
  --set minio.enabled=true \
  --set postgresMigration.enabled=true \
  --set minioMigration.enabled=true \
  --set keycloak.enabled=false \
  --set pgadmin.enabled=false \
  --set backend.enabled=false \
  --set frontend.enabled=false

wait_job_complete "quotation-book-postgres-migration"
wait_job_complete "quotation-book-minio-migration"

echo "[remote] Stage 3/4: keycloak"
helm_up \
  --set keycloak.enabled=true \
  --set backend.enabled=false \
  --set frontend.enabled=false
wait_pods "app.kubernetes.io/instance=$release,app.kubernetes.io/name=keycloak"

echo "[remote] Stage 4/4: app (backend/frontend/pgadmin)"
helm_up \
  --set backend.enabled=true \
  --set frontend.enabled=true \
  --set pgadmin.enabled=true

wait_pods "app.kubernetes.io/instance=$release,app.kubernetes.io/name=backend"
wait_pods "app.kubernetes.io/instance=$release,app.kubernetes.io/name=frontend"
wait_pods "app.kubernetes.io/instance=$release,app.kubernetes.io/name=pgadmin"

echo "[remote] OK"
kubectl -n "$ns" get pods,svc -o wide
REMOTE

echo "Done. If NodePort is enabled: https://$(echo "$MINIKUBE_HOST"):30443" || true
