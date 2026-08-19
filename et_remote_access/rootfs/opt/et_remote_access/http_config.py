"""Apply Home Assistant HTTP trusted-proxy settings via the Core WebSocket API."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any
from urllib.parse import urlparse

WS_URL = "ws://supervisor/core/websocket"
REQUIRED_PROXIES = ("172.16.0.0/12", "127.0.0.1/32", "::1/128")
META_KEYS = ("created_at", "error", "error_message")
HTTP_KEYS = (
    "server_host",
    "server_port",
    "ssl_certificate",
    "ssl_peer_certificate",
    "ssl_key",
    "cors_allowed_origins",
    "use_x_forwarded_for",
    "trusted_proxies",
    "login_attempts_threshold",
    "ip_ban_enabled",
    "ssl_profile",
    "use_x_frame_options",
)
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_RESTARTING = 10


def strip_meta(config: dict[str, Any] | None) -> dict[str, Any]:
    if not config:
        return {}
    return {key: value for key, value in config.items() if key not in META_KEYS}


def normalize_proxy(value: Any) -> str:
    text = str(value)
    if "/" not in text:
        if ":" in text:
            return f"{text}/128"
        return f"{text}/32"
    return text


def has_required_proxies(config: dict[str, Any] | None) -> bool:
    if not config:
        return False
    if not config.get("use_x_forwarded_for"):
        return False
    have = {normalize_proxy(item) for item in config.get("trusted_proxies") or []}
    return all(proxy in have for proxy in REQUIRED_PROXIES)


def merge_http_config(stable: dict[str, Any] | None) -> dict[str, Any]:
    cleaned = strip_meta(stable)
    merged = {key: cleaned[key] for key in HTTP_KEYS if key in cleaned}
    merged["use_x_forwarded_for"] = True
    proxies = [normalize_proxy(item) for item in merged.get("trusted_proxies") or []]
    for proxy in REQUIRED_PROXIES:
        if proxy not in proxies:
            proxies.append(proxy)
    merged["trusted_proxies"] = proxies
    return merged


def public_url(zrok_api: str, share_name: str) -> str:
    host = urlparse(zrok_api).hostname or ""
    if host.startswith("zrok2."):
        zone = host[len("zrok2.") :]
    else:
        zone = host
    return f"https://{share_name}.{zone}"


def share_token_for_name(payload: dict[str, Any], share_name: str) -> str | None:
    for share in payload.get("shares") or []:
        token = share.get("shareToken") or ""
        endpoints = share.get("frontendEndpoints") or []
        if share_name in token or any(share_name in str(item) for item in endpoints):
            return token or None
    return None


class CoreWs:
    def __init__(self, token: str) -> None:
        self._token = token
        self._ws: Any = None
        self._next_id = 1

    async def __aenter__(self) -> CoreWs:
        import websockets

        last_error: Exception | None = None
        for _ in range(30):
            try:
                self._ws = await websockets.connect(WS_URL, open_timeout=5)
                await self._auth()
                return self
            except Exception as err:  # noqa: BLE001 — retry until Core is up
                last_error = err
                await asyncio.sleep(2)
        raise RuntimeError(f"could not open Core websocket: {last_error}")

    async def __aexit__(self, *_exc: object) -> None:
        if self._ws is not None:
            await self._ws.close()

    async def _auth(self) -> None:
        hello = json.loads(await self._ws.recv())
        if hello.get("type") == "auth_ok":
            return
        if hello.get("type") != "auth_required":
            raise RuntimeError(f"unexpected websocket hello: {hello}")
        await self._ws.send(json.dumps({"type": "auth", "access_token": self._token}))
        result = json.loads(await self._ws.recv())
        if result.get("type") != "auth_ok":
            raise RuntimeError(f"websocket auth failed: {result}")

    async def call(self, payload: dict[str, Any]) -> dict[str, Any]:
        msg_id = self._next_id
        self._next_id += 1
        await self._ws.send(json.dumps({"id": msg_id, **payload}))
        while True:
            raw = json.loads(await self._ws.recv())
            if raw.get("id") != msg_id:
                continue
            if raw.get("type") == "result" and raw.get("success"):
                result = raw.get("result")
                return result if isinstance(result, dict) else {}
            if raw.get("type") == "result":
                raise RuntimeError(raw.get("error") or raw)
            raise RuntimeError(f"unexpected websocket reply: {raw}")


async def apply(external_url: str | None) -> int:
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        print("SUPERVISOR_TOKEN is missing", file=sys.stderr)
        return EXIT_ERROR

    async with CoreWs(token) as core:
        http_state = await core.call({"type": "http/config"})
        pending = http_state.get("pending")
        stable = http_state.get("stable")

        if pending and has_required_proxies(pending) and not pending.get("error"):
            print("pending HTTP config already has trusted proxies")
        elif not has_required_proxies(stable):
            merged = merge_http_config(stable)
            result = await core.call({"type": "http/config/configure", "config": merged})
            print("submitted HTTP trusted-proxy config")
            if result.get("restart"):
                print("waiting for Home Assistant to finish restarting")
                await asyncio.sleep(20)

    await _promote_and_set_url(token, external_url)
    return EXIT_OK


async def _promote_and_set_url(token: str, external_url: str | None) -> None:
    async with CoreWs(token) as core:
        http_state = await core.call({"type": "http/config"})
        pending = http_state.get("pending")
        if pending and has_required_proxies(pending) and not pending.get("error"):
            await core.call({"type": "http/config/promote"})
            print("promoted pending HTTP config")
        if external_url:
            await core.call({"type": "config/core/update", "external_url": external_url})
            print(f"set external_url to {external_url}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--external-url")
    parser.add_argument("--share-token-for")
    args = parser.parse_args()
    if args.share_token_for:
        data = json.load(sys.stdin)
        token = share_token_for_name(data, args.share_token_for)
        if token:
            print(token)
        return EXIT_OK
    try:
        return asyncio.run(apply(args.external_url))
    except Exception as err:  # noqa: BLE001
        print(err, file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
