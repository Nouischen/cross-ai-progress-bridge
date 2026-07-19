from __future__ import annotations

import hashlib
import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER_SHA256 = "F54D20B41681D9E1F044F78C3A0A2971537482F4216D5B2A2BAE01729EF8AC90"
PINNED_RAW_URL = (
    "https://raw.githubusercontent.com/Nouischen/"
    "cross-ai-progress-bridge/v1.0.0/bootstrap/install.py"
)
CANONICAL_INSTALL_PROMPT = "請直接在目前開啟的專案安裝 Cross-AI Progress Bridge，不要只解說。把 https://raw.githubusercontent.com/Nouischen/cross-ai-progress-bridge/v1.0.0/bootstrap/install.py 下載到作業系統暫存資料夾（不要存進專案），先驗證 SHA-256 必須完全等於 F54D20B41681D9E1F044F78C3A0A2971537482F4216D5B2A2BAE01729EF8AC90；不符就停止，不得換來源。用 Python 3.10 或更新版本執行已驗證的 install.py，`--target` 指向目前專案的絕對路徑；若缺少合格的 Python，先停止、不要修改專案，並用白話教我從官方來源安裝。若回傳 `INSTALL_NEEDS_CONSENT`，只列出偵測名稱並問我；只有我明確同意後，才用同一檔案加上 `--mode sidecar --accept-existing I_ACCEPT_SIDECAR` 重跑。不要叫我手動下載、解壓或搬檔，也不要自行讀取、搬移或覆蓋舊進度；最後回報 `INSTALL_OK` 或錯誤。"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(text: str, needle: str, label: str) -> None:
    assert needle in text, f"missing {label}: {needle!r}"


def forbid(text: str, needle: str, label: str) -> None:
    assert needle not in text, f"obsolete or unsafe {label}: {needle!r}"

def extract_markdown_prompt(text: str, label: str) -> str:
    match = re.search(
        r"\*\*複製從這裡開始\*\*\s*(?P<body>.*?)\s*\*\*複製到這裡結束\*\*",
        text,
        flags=re.DOTALL,
    )
    assert match, f"cannot extract Chinese installer prompt from {label}"
    lines = []
    for line in match.group("body").splitlines():
        stripped = line.strip()
        if stripped.startswith(">"):
            stripped = stripped[1:].lstrip()
        if stripped:
            lines.append(stripped)
    return " ".join(lines)


def extract_site_prompt(text: str) -> str:
    match = re.search(
        r'<div class="promptbox" id="install-prompt-zh">(?P<body>.*?)</div>',
        text,
        flags=re.DOTALL,
    )
    assert match, "cannot extract Chinese installer prompt from site"
    without_button = re.sub(r"<button\b.*?</button>", "", match.group("body"), flags=re.DOTALL)
    plain_text = re.sub(r"<[^>]+>", "", without_button)
    return html.unescape(plain_text).strip()


def main() -> None:
    required_files = [
        "README.md",
        "INSTALL.md",
        "SECURITY.md",
        "CHANGELOG.md",
        "LICENSE",
        "site/index.html",
        "bootstrap/install.py",
        "bootstrap/install.py.in",
        "tools/build_installer.py",
        "payload/entry.template.md",
        "payload/.ai-progress/bridge.py",
        "payload/.ai-progress/INSTRUCTIONS.md",
        "payload/AI_PROGRESS/README.md",
        "tests/test_bridge.py",
        "tests/test_install.py",
    ]
    for relative in required_files:
        assert (ROOT / relative).is_file(), f"missing file: {relative}"

    assert re.fullmatch(r"[0-9A-F]{64}", INSTALLER_SHA256), (
        "replace the INSTALLER_SHA256 release placeholder with the final "
        "uppercase SHA-256 before publishing"
    )
    installer_bytes = (ROOT / "bootstrap/install.py").read_bytes()
    actual_hash = hashlib.sha256(installer_bytes).hexdigest().upper()
    assert actual_hash == INSTALLER_SHA256, (
        "bootstrap/install.py drifted: "
        f"expected {INSTALLER_SHA256}, got {actual_hash}"
    )

    readme = read("README.md")
    install = read("INSTALL.md")
    security = read("SECURITY.md")
    changelog = read("CHANGELOG.md")
    site = read("site/index.html")
    public_docs = "\n".join((readme, install, security, changelog, site))


    prompts = {
        "README": extract_markdown_prompt(readme, "README"),
        "INSTALL": extract_markdown_prompt(install, "INSTALL"),
        "site": extract_site_prompt(site),
    }
    canonical_bytes = CANONICAL_INSTALL_PROMPT.encode("utf-8")
    for label, prompt in prompts.items():
        assert prompt == CANONICAL_INSTALL_PROMPT, (
            f"{label} Chinese installer prompt differs from the canonical text"
        )
        assert prompt.encode("utf-8") == canonical_bytes, (
            f"{label} Chinese installer prompt differs at the UTF-8 byte level"
        )
        for forbidden_token in ("```", "Code Block", "Markdown"):
            assert forbidden_token not in prompt, (
                f"{label} copied prompt contains forbidden token: {forbidden_token!r}"
            )
    assert len(set(prompts.values())) == 1, "Chinese installer prompts diverged"
    for text, label in [
        (readme, "README"),
        (install, "INSTALL"),
        (security, "SECURITY"),
        (site, "site"),
    ]:
        require(text, PINNED_RAW_URL, f"pinned installer URL in {label}")
        require(text, INSTALLER_SHA256, f"installer SHA-256 in {label}")

    for phrase in [
        "記錄進度",
        "繼續上次進度",
        "我有哪些進度還沒做完的",
    ]:
        require(readme, phrase, f"README command {phrase}")
        require(site, phrase, f"site command {phrase}")

    for phrase in [
        "同模型",
        "跨模型",
        "Claude Code",
        "Codex",
        "Python 3.10",
        "同一個實體資料夾",
        "不用手動下載",
        "sidecar",
        "接力：",
        "I_ACCEPT_SIDECAR",
    ]:
        require(readme, phrase, f"README setup claim {phrase}")
        require(site, phrase, f"site setup claim {phrase}")

    for phrase in [
        ".ai-progress/bridge.py",
        "AI_PROGRESS/tasks/",
        "INSTALL_NEEDS_CONSENT",
        "--mode sidecar --accept-existing I_ACCEPT_SIDECAR",
        "不讀取、不搬移、不轉換、不覆蓋",
    ]:
        require(readme, phrase, f"README architecture claim {phrase}")
        require(install, phrase, f"INSTALL architecture claim {phrase}")

    for obsolete in [
        "/v1.0.0/INSTALL.md",
        "AI_SYSTEM/",
        "NOT READY",
        "重設驗證",
        "protocol 3.9",
        "已通過 Claude Code／Codex 端到端",
        "驗證接力",
        "完成驗證",
        "claimed-fresh",
    ]:
        forbid(public_docs, obsolete, "release documentation")

    require(site, 'name="viewport"', "responsive viewport")
    require(site, "navigator.clipboard", "clipboard API")
    require(site, "document.execCommand('copy')", "clipboard fallback")
    require(site, "@media (max-width: 760px)", "mobile breakpoint")
    require(site, 'lang="zh-Hant"', "Traditional Chinese document language")

    assert not re.search(r"<script[^>]+src=", site, flags=re.IGNORECASE), (
        "landing page must not load external scripts"
    )
    for analytics_marker in ("google-analytics", "gtag(", "facebook.com/tr"):
        assert analytics_marker not in site.lower(), (
            f"landing page contains analytics marker: {analytics_marker}"
        )

    gitattributes = read(".gitattributes")
    require(gitattributes, "INSTALL.md text eol=lf", "INSTALL.md LF rule")
    forbid(gitattributes, "INSTALL.md -text", "INSTALL.md binary rule")

    forbidden_secret_shapes = [
        r"github_pat_[A-Za-z0-9_]{20,}",
        r"ghp_[A-Za-z0-9]{20,}",
        r"AKIA[0-9A-Z]{16}",
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    ]
    public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
        and (path.suffix.lower() in {".md", ".py", ".yml", ".yaml", ".html", ".svg"} or path.name == "LICENSE")
    )
    for pattern in forbidden_secret_shapes:
        assert not re.search(pattern, public_text), f"secret-like pattern found: {pattern}"

    assert "C:\\Users\\USER" not in public_text
    assert "C:\\ObsidianVault" not in public_text
    print("PASS: deterministic installer, public docs, landing page, and safety checks")


if __name__ == "__main__":
    main()
