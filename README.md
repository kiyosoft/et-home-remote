# Et Remote Access

Home Assistant OS add-on that shares this instance through a **self-hosted zrok2** overlay (the same Nabu Casa-style URL as `mint-home`).

It does **not** use zrok.io and does not deploy AWS. Paste the JSON fields from `sudo mint-home` on the overlay host.

## Install

### Local (HAOS in VirtualBox)

Copy the `et_remote_access` folder onto the HA host as `/addons/et_remote_access` (Samba **addons** share), then refresh the add-on store. It appears under **Local add-ons**.

### From git (Add-on store)

1. Push this repository somewhere Home Assistant can clone.
2. Set `url` in `repository.yaml` to that git URL.
3. In Home Assistant: **Settings → Add-ons → Add-on store → ⋮ → Repositories** and paste the URL.
4. Install **Et Remote Access**.

### Options

From mint-home JSON:

- `zrok_api` → `zrokApi`
- `enable_token` → `enableToken`
- `share_name` → `shareName`
- `target` → `http://homeassistant:8123` (leave this unless Core is on another port)

Start the add-on. Check the log for `Sharing http://homeassistant:8123`. If you only see HTTP proxy messages and then nothing, rebuild/restart the add-on after pulling this `run.sh` fix (do not leave it stuck waiting).

Open `https://<shareName>.home.feedbyte.io` from a phone off this Wi‑Fi.

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
