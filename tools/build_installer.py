from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "bootstrap" / "install.py.in"
OUTPUT = ROOT / "bootstrap" / "install.py"
PAYLOAD_ROOT = ROOT / "payload"
PAYLOAD_FILES = (
    ".ai-progress/bridge.py",
    ".ai-progress/INSTRUCTIONS.md",
    "AI_PROGRESS/README.md",
    "entry.template.md",
)


def build_text() -> str:
    payload: dict[str, str] = {}
    for relative in PAYLOAD_FILES:
        path = PAYLOAD_ROOT / relative
        payload[relative] = path.read_text(encoding="utf-8").replace("\r\n", "\n")

    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    encoded = base64.b64encode(raw).decode("ascii")
    digest = hashlib.sha256(raw).hexdigest().upper()

    template = TEMPLATE.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert template.count("__PAYLOAD_B64__") == 1
    assert template.count("__PAYLOAD_SHA256__") == 1
    return template.replace("__PAYLOAD_B64__", encoded).replace(
        "__PAYLOAD_SHA256__", digest
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the standalone installer")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = build_text()

    if args.check:
        if not OUTPUT.is_file():
            raise SystemExit("bootstrap/install.py is missing")
        current = OUTPUT.read_text(encoding="utf-8").replace("\r\n", "\n")
        if current != rendered:
            raise SystemExit("bootstrap/install.py is stale; run tools/build_installer.py")
        print("PASS: bootstrap/install.py matches canonical raw payload sources")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(rendered, encoding="utf-8", newline="\n")
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest().upper()
    print(f"wrote {OUTPUT}")
    print(f"SHA-256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
