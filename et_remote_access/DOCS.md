# Et Remote Access

Shares this Home Assistant over a self-hosted zrok2 overlay. You need a home minted on the overlay (`sudo mint-home`), not a zrok.io account.

## Configuration

Paste values from mint-home JSON:

| Option | mint-home field |
| --- | --- |
| zrok API | `zrokApi` |
| Enable token | `enableToken` |
| Share name | `shareName` |
| Local target | usually `http://homeassistant:8123` |

The public URL is `https://<shareName>.home.<your overlay zone>`.

On first start the add-on updates **Settings → System → Network → HTTP server** (trusted proxies + X-Forwarded-For) through the Core API. Home Assistant restarts once; the add-on then confirms the settings so they do not roll back. Do not put an `http:` block in `configuration.yaml` — Home Assistant ignores it after the 2026.8 migration.

Leave the add-on running. Stopping it ends the share.

If the public page is **400**, trusted proxies were not promoted. If **502**, Core is not reachable at `target` or the share process exited — check the add-on log.
