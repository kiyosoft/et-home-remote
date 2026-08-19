import sys
import unittest
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "rootfs" / "opt" / "et_remote_access"),
)

from http_config import (
    has_required_proxies,
    merge_http_config,
    public_url,
    share_token_for_name,
)


class HttpConfigTest(unittest.TestCase):
    def test_merges_required_proxies_without_dropping_port(self) -> None:
        merged = merge_http_config(
            {
                "server_port": 80,
                "created_at": "ignore-me",
                "use_x_forwarded_for": False,
                "trusted_proxies": ["192.168.100.161"],
            }
        )
        self.assertTrue(merged["use_x_forwarded_for"])
        self.assertEqual(merged["server_port"], 80)
        self.assertNotIn("created_at", merged)
        self.assertIn("172.16.0.0/12", merged["trusted_proxies"])
        self.assertIn("192.168.100.161/32", merged["trusted_proxies"])

    def test_detects_required_proxies(self) -> None:
        self.assertFalse(has_required_proxies({"use_x_forwarded_for": True}))
        self.assertTrue(
            has_required_proxies(
                {
                    "use_x_forwarded_for": True,
                    "trusted_proxies": [
                        "172.16.0.0/12",
                        "127.0.0.1",
                        "::1",
                    ],
                }
            )
        )

    def test_public_url_strips_zrok2_label(self) -> None:
        self.assertEqual(
            public_url(
                "https://zrok2.home.feedbyte.io",
                "home-9756220a791de7da38c3857591a6c608",
            ),
            "https://home-9756220a791de7da38c3857591a6c608.home.feedbyte.io",
        )

    def test_share_token_lookup(self) -> None:
        token = share_token_for_name(
            {
                "shares": [
                    {
                        "shareToken": "abc123",
                        "frontendEndpoints": [
                            "home-9756220a791de7da38c3857591a6c608.home.feedbyte.io"
                        ],
                    }
                ]
            },
            "home-9756220a791de7da38c3857591a6c608",
        )
        self.assertEqual(token, "abc123")


if __name__ == "__main__":
    unittest.main()
