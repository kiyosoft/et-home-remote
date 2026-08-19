# Et Remote Access

Home Assistant OS add-on that shares this instance through a **self-hosted zrok2** overlay (the same Nabu Casa-style URL as `mint-home`).

It does **not** use zrok.io and does not deploy AWS. Paste the JSON fields from `sudo mint-home` on the overlay host.

## Install

1. In Home Assistant: **Settings → Add-ons → Add-on store → ⋮ → Repositories**
2. Add this git repository URL
3. Install **Et Remote Access**
4. Set options from mint-home:
   - `zrok_api` → `zrokApi`
   - `enable_token` → `enableToken`
   - `share_name` → `shareName`
   - `target` → `http://homeassistant:8123` (leave this unless Core is on another port)
5. Start the add-on. The first start may restart Home Assistant once to set trusted proxies, then start again and promote that config automatically.
6. Open `https://<shareName>.home.feedbyte.io` from a phone off this Wi‑Fi.

## Outbound access

The add-on only makes outbound connections:

- TCP 443 to the zrok API host
- TCP 1280 to `ziti.<home zone>`
- TCP 3022 to `router.<home zone>`

## Development

```bash
cd et_remote_access
PYTHONPATH=rootfs/opt/et_remote_access python3 -m unittest tests.test_http_config
```
