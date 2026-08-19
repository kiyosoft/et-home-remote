#!/command/with-contenv bashio
set -euo pipefail

export HOME=/data
ZROK2_API_ENDPOINT="$(bashio::config 'zrok_api')"
export ZROK2_API_ENDPOINT
ENABLE_TOKEN="$(bashio::config 'enable_token')"
SHARE_NAME="$(bashio::config 'share_name')"
TARGET="$(bashio::config 'target')"

if ! [[ "${SHARE_NAME}" =~ ^home-[0-9a-f]{32}$ ]]; then
  bashio::exit.nok "share_name must look like home-<32 hex chars> from mint-home"
fi
if [[ -z "${ENABLE_TOKEN}" || "${ENABLE_TOKEN}" == "null" ]]; then
  bashio::exit.nok "enable_token is required (mint-home enableToken)"
fi

HOST="${ZROK2_API_ENDPOINT#https://}"
HOST="${HOST#http://}"
HOST="${HOST%%/*}"
if [[ "${HOST}" == zrok2.* ]]; then
  ZONE="${HOST#zrok2.}"
else
  ZONE="${HOST}"
fi
PUBLIC_URL="https://${SHARE_NAME}.${ZONE}"

bashio::log.info "Public URL will be ${PUBLIC_URL}"
bashio::log.info "Applying Home Assistant HTTP trusted proxies if needed"

set +e
python3 /opt/et_remote_access/http_config.py --external-url "${PUBLIC_URL}"
HTTP_RC=$?
set -e
if [[ "${HTTP_RC}" -ne 0 ]]; then
  bashio::log.warning "HTTP proxy update failed (exit ${HTTP_RC}). The public URL may return 400 until trusted proxies are set."
fi
bashio::log.info "Starting zrok2 share"

if [[ ! -f "${HOME}/.zrok2/environment.json" ]]; then
  bashio::log.info "Enabling zrok2 environment"
  zrok2 enable --headless "${ENABLE_TOKEN}"
else
  bashio::log.info "zrok2 environment already enabled"
fi

if zrok2 create name -n public "${SHARE_NAME}"; then
  bashio::log.info "Reserved name ${SHARE_NAME}"
else
  bashio::log.info "Name ${SHARE_NAME} already exists; continuing"
fi

cleanup_orphan_share() {
  local token
  token="$(
    zrok2 list shares --json 2>/dev/null \
      | python3 /opt/et_remote_access/http_config.py --share-token-for "${SHARE_NAME}" \
      || true
  )"
  if [[ -n "${token}" ]]; then
    bashio::log.info "Deleting leftover share"
    zrok2 delete share "${token}" || true
  fi
}

SHARE_PID=""
shutdown() {
  if [[ -n "${SHARE_PID}" ]] && kill -0 "${SHARE_PID}" 2>/dev/null; then
    kill -TERM "${SHARE_PID}" 2>/dev/null || true
    wait "${SHARE_PID}" 2>/dev/null || true
  fi
  exit 0
}
trap shutdown SIGTERM SIGINT

backoff=2
while true; do
  bashio::log.info "Sharing ${TARGET} as public:${SHARE_NAME}"
  set +e
  zrok2 share public "${TARGET}" -n "public:${SHARE_NAME}" &
  SHARE_PID=$!
  wait "${SHARE_PID}"
  rc=$?
  SHARE_PID=""
  set -e
  if [[ "${rc}" -ne 0 ]]; then
    bashio::log.warning "Share exited ${rc}; checking for a leftover share"
    cleanup_orphan_share
  fi
  sleep "${backoff}"
  if [[ "${backoff}" -lt 60 ]]; then
    backoff=$((backoff * 2))
  fi
done
