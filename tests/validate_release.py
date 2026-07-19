from __future__ import annotations

import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALL_HASH = "62B052F6791BDA02C6749B3FD8FEDF320C3A4EE969EC8D32C432E438032C4FA2"
PINNED_RAW_URL = (
    "https://raw.githubusercontent.com/Nouischen/"
    "cross-ai-progress-bridge/v1.0.0/INSTALL.md"
)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(text: str, needle: str, label: str) -> None:
    assert needle in text, f"missing {label}: {needle!r}"


def main() -> None:
    required_files = [
        "README.md",
        "INSTALL.md",
        "SECURITY.md",
        "CHANGELOG.md",
        "LICENSE",
        "site/index.html",
    ]
    for relative in required_files:
        assert (ROOT / relative).is_file(), f"missing file: {relative}"

    install_bytes = (ROOT / "INSTALL.md").read_bytes()
    actual_hash = hashlib.sha256(install_bytes).hexdigest().upper()
    assert actual_hash == INSTALL_HASH, (
        f"INSTALL.md drifted: expected {INSTALL_HASH}, got {actual_hash}"
    )

    readme = read("README.md")
    security = read("SECURITY.md")
    site = read("site/index.html")

    for text, label in [(readme, "README"), (security, "SECURITY"), (site, "site")]:
        require(text, PINNED_RAW_URL, f"pinned installer URL in {label}")
        require(text, INSTALL_HASH, f"installer SHA-256 in {label}")

    for phrase in [
        "記錄進度",
        "繼續上次進度",
        "我有哪些進度還沒做完的",
        "驗證接力",
        "完成驗證",
        "重設驗證",
    ]:
        require(readme, phrase, f"README command {phrase}")
        require(site, phrase, f"site command {phrase}")

    for phrase in [
        "同模型",
        "跨模型",
        "Claude Code",
        "Codex",
        "不需要 Obsidian",
        "既有系統",
    ]:
        require(readme, phrase, f"README claim {phrase}")
        require(site, phrase, f"site claim {phrase}")

    require(site, 'name="viewport"', "responsive viewport")
    require(site, "navigator.clipboard", "clipboard API")
    require(site, "document.execCommand('copy')", "clipboard fallback")
    require(site, "@media (max-width: 760px)", "mobile breakpoint")
    require(site, 'lang="zh-Hant"', "Traditional Chinese document language")

    assert not re.search(r"<script[^>]+src=", site, flags=re.IGNORECASE), (
        "landing page must not load external scripts"
    )
    assert "google-analytics" not in site.lower()
    assert "gtag(" not in site.lower()
    assert "facebook.com/tr" not in site.lower()

    forbidden_secret_shapes = [
        r"github_pat_[A-Za-z0-9_]{20,}",
        r"ghp_[A-Za-z0-9]{20,}",
        r"AKIA[0-9A-Z]{16}",
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    ]
    public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts
    )
    for pattern in forbidden_secret_shapes:
        assert not re.search(pattern, public_text), f"secret-like pattern found: {pattern}"

    assert "C:\\Users\\USER" not in public_text
    assert "C:\\ObsidianVault" not in public_text
    print("PASS: release package, pinned installer, landing page, and safety checks")


if __name__ == "__main__":
    main()
