import unittest
from pathlib import Path

ADDON_DIR = Path(__file__).resolve().parents[1]


class PackagingTest(unittest.TestCase):
    def test_uses_debian_base_for_glibc_zrok2(self) -> None:
        build = (ADDON_DIR / "build.yaml").read_text()
        self.assertIn("base-debian", build)
        self.assertNotRegex(build, r"base:\d")

    def test_dockerfile_installs_glibc_packages_and_probes_zrok2(self) -> None:
        dockerfile = (ADDON_DIR / "Dockerfile").read_text()
        self.assertIn("apt-get", dockerfile)
        self.assertNotIn("apk add", dockerfile)
        self.assertIn("/usr/local/bin/zrok2 version", dockerfile)
