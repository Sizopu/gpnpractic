#!/usr/bin/env sh
set -eu

TEMPLATE_PATH="${1:-quotation-book/ci/values-from-env.tpl.yaml}"
OUT_PATH="${2:-/tmp/values-ci.yaml}"

b64() {

  base64 < "$1" | tr -d '\n'
}

if [ "${TLS_CERTIFICATE_CRT_FILE:-}" != "" ]; then
  export TLS_CERTIFICATE_CRT_B64="$(b64 "$TLS_CERTIFICATE_CRT_FILE")"
fi
if [ "${TLS_PRIVATE_KEY_FILE:-}" != "" ]; then
  export TLS_PRIVATE_KEY_B64="$(b64 "$TLS_PRIVATE_KEY_FILE")"
fi
if [ "${TLS_CA_ROOT_CRT_FILE:-}" != "" ]; then
  export TLS_CA_ROOT_CRT_B64="$(b64 "$TLS_CA_ROOT_CRT_FILE")"
fi

# Render values
envsubst < "$TEMPLATE_PATH" > "$OUT_PATH"

echo "Rendered: $OUT_PATH"
