from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "bootstrap" / "install.py"
BUILDER = ROOT / "tools" / "build_installer.py"


def run_install(target: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(INSTALLER), "--target", str(target), *args],
        cwd=target,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
        env=env,
    )


def load_template_installer(temp_dir: Path):
    """Load the current template without changing the checked-in generated installer."""
    spec = importlib.util.spec_from_file_location(
        "progress_bridge_installer_test", temp_dir / "installer.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render_template_installer(temp_dir: Path) -> object:
    import tools.build_installer as builder

    path = temp_dir / "installer.py"
    path.write_text(builder.build_text(), encoding="utf-8", newline="\n")
    return load_template_installer(temp_dir)


class InstallerTests(unittest.TestCase):
    def test_rollback_restore_failure_preserves_install_backup_for_manual_recovery(self) -> None:
        with tempfile.TemporaryDirectory(prefix="progress-bridge-rollback-") as raw:
            workspace = Path(raw)
            target = workspace / "target"
            target.mkdir()
            entry = target / "CLAUDE.md"
            original = b"# Existing rules\n\nKeep these bytes.\n"
            entry.write_bytes(original)
            installer = render_template_installer(workspace)
            original_atomic_write = installer.atomic_write

            def inject_failure(path, data, mode=None):
                if path.name == "AGENTS.md":
                    raise OSError("injected later entry failure")
                if path.name == "CLAUDE.md" and data == original:
                    raise OSError("injected entry restore failure")
                return original_atomic_write(path, data, mode)

            installer.atomic_write = inject_failure
            with self.assertRaises(installer.InstallError) as raised:
                installer.install(target, "sidecar", installer.decode_payload())

            self.assertIn("rollback was incomplete", str(raised.exception))
            self.assertIn("manually restore", str(raised.exception))
            self.assertTrue(entry.read_bytes().startswith(original))
            self.assertIn(b"CROSS-AI-PROGRESS-BRIDGE:START", entry.read_bytes())
            backups = list(
                (target / ".ai-progress/backups/install").glob("CLAUDE.md.*.bak")
            )
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), original)
            self.assertTrue((target / ".ai-progress").is_dir())
            self.assertTrue((target / "AI_PROGRESS").is_dir())

    def test_normal_rollback_cleans_new_roots_after_later_entry_failure(self) -> None:
        with tempfile.TemporaryDirectory(prefix="progress-bridge-clean-rollback-") as raw:
            workspace = Path(raw)
            target = workspace / "target"
            target.mkdir()
            entry = target / "CLAUDE.md"
            original = b"# Existing rules\n"
            entry.write_bytes(original)
            installer = render_template_installer(workspace)
            original_atomic_write = installer.atomic_write

            def inject_failure(path, data, mode=None):
                if path.name == "AGENTS.md":
                    raise OSError("injected later entry failure")
                return original_atomic_write(path, data, mode)

            installer.atomic_write = inject_failure
            with self.assertRaises(OSError) as raised:
                installer.install(target, "sidecar", installer.decode_payload())

            self.assertIn("injected later entry failure", str(raised.exception))
            self.assertEqual(entry.read_bytes(), original)
            self.assertFalse((target / ".ai-progress").exists())
            self.assertFalse((target / "AI_PROGRESS").exists())
    def test_fresh_install_and_idempotent_rerun(self) -> None:
        with tempfile.TemporaryDirectory(prefix="progress-bridge-fresh-") as raw:
            target = Path(raw)
            first = run_install(target)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertIn("INSTALL_OK", first.stdout)

            required = [
                ".ai-progress/bridge.py",
                ".ai-progress/INSTRUCTIONS.md",
                "AI_PROGRESS/README.md",
                "AI_PROGRESS/config.json",
                "CLAUDE.md",
                "AGENTS.md",
            ]
            for relative in required:
                self.assertTrue((target / relative).is_file(), relative)

            self.assertTrue((target / "AI_PROGRESS/locks").is_dir())
            self.assertFalse((target / "AI_PROGRESS/verification").exists())
            config = json.loads((target / "AI_PROGRESS/config.json").read_text("utf-8"))
            self.assertEqual(config["mode"], "fresh")
            self.assertEqual(config["trigger_prefix"], "")
            self.assertNotIn("verification_status", config)
            self.assertEqual(
                (target / "CLAUDE.md").read_text("utf-8").count(
                    "<!-- CROSS-AI-PROGRESS-BRIDGE:START -->"
                ),
                1,
            )

            second = run_install(target)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("ALREADY_INSTALLED", second.stdout)

    def test_existing_system_requires_consent_and_stays_untouched(self) -> None:
        with tempfile.TemporaryDirectory(prefix="progress-bridge-consent-") as raw:
            target = Path(raw)
            original = b"# My existing rules\n\nDo not replace me.\n"
            entry = target / "CLAUDE.md"
            entry.write_bytes(original)

            probe = run_install(target)
            self.assertEqual(probe.returncode, 20, probe.stderr)
            self.assertIn("INSTALL_NEEDS_CONSENT", probe.stdout)
            self.assertIn("- CLAUDE.md", probe.stdout)
            self.assertEqual(entry.read_bytes(), original)
            self.assertFalse((target / ".ai-progress").exists())
            self.assertFalse((target / "AI_PROGRESS").exists())

            denied = run_install(target, "--mode", "sidecar")
            self.assertNotEqual(denied.returncode, 0)
            self.assertEqual(entry.read_bytes(), original)
            self.assertFalse((target / ".ai-progress").exists())

            accepted = run_install(
                target,
                "--mode",
                "sidecar",
                "--accept-existing",
                "I_ACCEPT_SIDECAR",
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            updated = entry.read_bytes()
            self.assertTrue(updated.startswith(original))
            self.assertIn(
                b"Only route commands that begin with `" + "接力：".encode("utf-8") + b"`",
                updated,
            )
            config = json.loads((target / "AI_PROGRESS/config.json").read_text("utf-8"))
            self.assertEqual(config["mode"], "sidecar")
            self.assertEqual(config["trigger_prefix"], "接力：")

            backups = list(
                (target / ".ai-progress/backups/install").glob("CLAUDE.md.*.bak")
            )
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), original)

    def test_dot_claude_requires_consent_without_writes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="progress-bridge-dot-claude-") as raw:
            target = Path(raw)
            (target / ".claude").mkdir()
            before = sorted(item.name for item in target.iterdir())
            result = run_install(target)
            self.assertEqual(result.returncode, 20, result.stderr)
            self.assertIn("- .claude", result.stdout)
            self.assertEqual(sorted(item.name for item in target.iterdir()), before)
            self.assertFalse((target / ".ai-progress").exists())
            self.assertFalse((target / "AI_PROGRESS").exists())

    def test_sidecar_preserves_bom_crlf_bytes_backup_and_mode(self) -> None:
        with tempfile.TemporaryDirectory(prefix="progress-bridge-bom-") as raw:
            target = Path(raw)
            entry = target / "CLAUDE.md"
            original = b"\xef\xbb\xbf# Existing rules\r\n\r\nKeep exact bytes.\r\n"
            entry.write_bytes(original)
            if os.name != "nt":
                entry.chmod(0o640)
            original_mode = stat.S_IMODE(entry.stat().st_mode)

            accepted = run_install(
                target,
                "--mode",
                "sidecar",
                "--accept-existing",
                "I_ACCEPT_SIDECAR",
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            updated = entry.read_bytes()
            self.assertTrue(updated.startswith(original))
            appended = updated[len(original) :]
            self.assertNotIn(b"\n", appended.replace(b"\r\n", b""))
            self.assertEqual(stat.S_IMODE(entry.stat().st_mode), original_mode)

            backups = list(
                (target / ".ai-progress/backups/install").glob("CLAUDE.md.*.bak")
            )
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), original)

    def test_malformed_utf8_entry_fails_cleanly_without_changes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="progress-bridge-utf8-") as raw:
            target = Path(raw)
            entry = target / "CLAUDE.md"
            original = b"\xff\xfeinvalid"
            entry.write_bytes(original)
            result = run_install(
                target,
                "--mode",
                "sidecar",
                "--accept-existing",
                "I_ACCEPT_SIDECAR",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("entry file is not UTF-8", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertEqual(len(result.stderr.strip().splitlines()), 1)
            self.assertEqual(entry.read_bytes(), original)
            self.assertFalse((target / ".ai-progress").exists())
            self.assertFalse((target / "AI_PROGRESS").exists())

    def test_progress_name_alone_triggers_consent(self) -> None:
        with tempfile.TemporaryDirectory(prefix="progress-bridge-existing-") as raw:
            target = Path(raw)
            (target / "progress").mkdir()
            result = run_install(target)
            self.assertEqual(result.returncode, 20)
            self.assertIn("- progress", result.stdout)
            self.assertFalse((target / ".ai-progress").exists())

    def test_owned_file_drift_refuses_repair(self) -> None:
        with tempfile.TemporaryDirectory(prefix="progress-bridge-drift-") as raw:
            target = Path(raw)
            first = run_install(target)
            self.assertEqual(first.returncode, 0, first.stderr)
            bridge = target / ".ai-progress/bridge.py"
            bridge.write_text(bridge.read_text("utf-8") + "# local drift\n", "utf-8")
            rerun = run_install(target)
            self.assertNotEqual(rerun.returncode, 0)
            self.assertIn("refusing automatic repair", rerun.stderr)

    def test_entry_symlink_is_rejected_when_supported(self) -> None:
        with tempfile.TemporaryDirectory(prefix="progress-bridge-link-") as raw:
            target = Path(raw)
            source = target / "real-rules.md"
            source.write_text("original\n", encoding="utf-8")
            link = target / "CLAUDE.md"
            try:
                link.symlink_to(source.name)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation is unavailable")

            result = run_install(
                target,
                "--mode",
                "sidecar",
                "--accept-existing",
                "I_ACCEPT_SIDECAR",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("link/junction/reparse", result.stderr)
            self.assertEqual(source.read_text("utf-8"), "original\n")
            self.assertFalse((target / ".ai-progress").exists())

    def test_generated_installer_uses_raw_base64_and_is_current(self) -> None:
        text = INSTALLER.read_text(encoding="utf-8")
        self.assertNotIn("import gzip", text)
        self.assertNotIn("gzip.decompress", text)
        before = hashlib.sha256(INSTALLER.read_bytes()).hexdigest()
        result = subprocess.run(
            [sys.executable, str(BUILDER), "--check"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("canonical raw payload", result.stdout)
        self.assertEqual(hashlib.sha256(INSTALLER.read_bytes()).hexdigest(), before)


if __name__ == "__main__":
    unittest.main()
