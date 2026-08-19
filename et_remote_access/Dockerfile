ARG BUILD_FROM
FROM ${BUILD_FROM}

ARG BUILD_ARCH
ARG BUILD_VERSION
ARG ZROK_VERSION=2.0.4

RUN set -eux; \
  case "${BUILD_ARCH}" in \
    amd64) ZROK_ARCH=amd64 ;; \
    aarch64) ZROK_ARCH=arm64 ;; \
    *) echo "unsupported arch: ${BUILD_ARCH}" >&2; exit 1 ;; \
  esac; \
  apt-get update; \
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    python3 \
    python3-websockets; \
  rm -rf /var/lib/apt/lists/*; \
  curl -fsSL \
    "https://github.com/openziti/zrok/releases/download/v${ZROK_VERSION}/zrok_${ZROK_VERSION}_linux_${ZROK_ARCH}.tar.gz" \
    | tar -xz -C /usr/local/bin zrok2; \
  chmod +x /usr/local/bin/zrok2; \
  /usr/local/bin/zrok2 version

COPY rootfs/ /

RUN chmod a+x /run.sh

LABEL \
  io.hass.name="Et Remote Access" \
  io.hass.description="Share Home Assistant through a self-hosted zrok2 overlay" \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="addon" \
  io.hass.arch="aarch64|amd64"

CMD ["/run.sh"]
