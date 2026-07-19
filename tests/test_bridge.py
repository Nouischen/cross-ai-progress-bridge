import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
BRIDGE_SOURCE = REPO / "payload" / ".ai-progress" / "bridge.py"


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "project"
        self.bridge_dir = self.root / ".ai-progress"
        self.bridge_dir.mkdir(parents=True)
        self.bridge = self.bridge_dir / "bridge.py"
        shutil.copy2(BRIDGE_SOURCE, self.bridge)
        self.env = os.environ.copy()
        self.env["PYTHONIOENCODING"] = "utf-8"

    def tearDown(self):
        self.temp.cleanup()

    def command(self, *args):
        return [sys.executable, str(self.bridge), *args]

    def invoke(self, *args, ok=True):
        result = subprocess.run(
            self.command(*args),
            cwd=self.root.parent,
            text=True,
            encoding="utf-8",
            capture_output=True,
            env=self.env,
            check=False,
        )
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        return result

    def load_bridge_module(self):
        name = f"bridge_under_test_{time.time_ns()}"
        spec = importlib.util.spec_from_file_location(name, self.bridge)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def draft(self, name, **values):
        folder = self.root / "AI_PROGRESS" / "drafts"
        folder.mkdir(parents=True, exist_ok=True)
        base = {
            "title": "Release checklist",
            "status": "active",
            "goal": "ship",
            "progress": "started",
            "next_steps": "test",
            "blockers": "",
            "decisions": "",
            "verification": "",
            "related_files": "",
            "rerun": "",
        }
        base.update(values)
        (folder / name).write_text(
            json.dumps(base, ensure_ascii=False), encoding="utf-8"
        )

    def test_root_is_script_anchored_and_public_root_argument_is_rejected(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        result = subprocess.run(
            self.command("--root", str(outside), "status"),
            cwd=outside,
            text=True,
            encoding="utf-8",
            capture_output=True,
            env=self.env,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("bridge.py: error:", result.stderr)
        self.assertFalse((outside / "AI_PROGRESS").exists())
        self.assertFalse((self.root / "AI_PROGRESS").exists())

        status = self.invoke("status")
        self.assertEqual(status["open"], [])
        self.assertTrue((self.root / "AI_PROGRESS" / "config.json").is_file())
        self.assertFalse((self.root.parent / "AI_PROGRESS").exists())

    def test_fresh_create_update_and_backup(self):
        self.invoke("status")
        self.draft("new.json")
        saved = self.invoke("save", "--draft", "new.json")
        self.assertEqual(saved["revision"], 1)
        shown = self.invoke("show", saved["id"])
        self.assertEqual(shown["title"], "Release checklist")
        self.draft(
            "update.json",
            id=saved["id"],
            expected_revision=1,
            progress="done",
        )
        updated = self.invoke("save", "--draft", "update.json")
        self.assertEqual(updated["revision"], 2)
        self.assertTrue(list((self.root / "AI_PROGRESS" / "backups").glob("*.md")))
        self.assertTrue(
            (self.root / "AI_PROGRESS" / "locks" / f"{saved['id']}.lock").is_file()
        )

    def test_conflict_preserves_task_and_writes_conflict(self):
        self.invoke("status")
        self.draft("new.json")
        saved = self.invoke("save", "--draft", "new.json")
        self.draft("stale.json", id=saved["id"], expected_revision=0)
        result = self.invoke("save", "--draft", "stale.json")
        self.assertEqual(result["result"], "conflict")
        self.assertEqual(self.invoke("show", saved["id"])["revision"], 1)
        self.assertTrue(list((self.root / "AI_PROGRESS" / "conflicts").glob("*.json")))

    def test_distinct_unicode_titles_get_distinct_stable_ids(self):
        self.invoke("status")
        first_title = "診所網站首頁改版"
        second_title = "診所網站付款頁改版"
        self.draft("first.json", title=first_title)
        self.draft("second.json", title=second_title)
        first = self.invoke("save", "--draft", "first.json")
        second = self.invoke("save", "--draft", "second.json")

        self.assertNotEqual(first["id"], second["id"])
        self.assertRegex(first["id"], r"^[a-z0-9][a-z0-9_-]{0,79}$")
        self.assertRegex(second["id"], r"^[a-z0-9][a-z0-9_-]{0,79}$")
        self.assertLess(len(first["id"]), 80)
        bridge = self.load_bridge_module()
        self.assertEqual(bridge.slug(first_title), first["id"])
        self.assertEqual(bridge.slug(first_title), bridge.slug(first_title))

    def test_list_open_and_revision_guarded_archive(self):
        self.invoke("status")
        self.draft("one.json", title="Open", status="active")
        self.draft("two.json", title="Blocked", status="blocked")
        self.draft("three.json", title="Done", status="completed")
        one = self.invoke("save", "--draft", "one.json")
        self.invoke("save", "--draft", "two.json")
        self.invoke("save", "--draft", "three.json")
        listed = self.invoke("list", "--open")["tasks"]
        self.assertEqual({item["status"] for item in listed}, {"active", "blocked"})
        self.assertTrue(all(item.get("updated_at") for item in listed))

        missing_revision = self.invoke("archive", one["id"], ok=False)
        self.assertIn("--expected-revision", missing_revision.stderr)
        wrong = self.invoke(
            "archive", one["id"], "--expected-revision", "0", ok=False
        )
        self.assertIn("archive revision conflict", wrong.stderr)
        self.assertTrue((self.root / "AI_PROGRESS" / "tasks" / f"{one['id']}.md").is_file())

        archived = self.invoke(
            "archive", one["id"], "--expected-revision", str(one["revision"])
        )
        self.assertEqual(archived["revision"], 2)
        shown = self.invoke("show", one["id"])
        self.assertEqual(shown["status"], "archived")
        self.assertEqual(shown["revision"], 2)
        self.assertFalse(
            (self.root / "AI_PROGRESS" / "tasks" / f"{one['id']}.md").exists()
        )
        self.assertTrue(
            (self.root / "AI_PROGRESS" / "archive" / f"{one['id']}.md").is_file()
        )

    def test_preexisting_archive_target_never_mutates_active_source(self):
        self.invoke("status")
        self.draft("new.json")
        saved = self.invoke("save", "--draft", "new.json")
        source = self.root / "AI_PROGRESS" / "tasks" / f"{saved['id']}.md"
        original = source.read_bytes()
        target = self.root / "AI_PROGRESS" / "archive" / f"{saved['id']}.md"
        sentinel = b"existing archive target\n"
        target.write_bytes(sentinel)

        result = self.invoke(
            "archive",
            saved["id"],
            "--expected-revision",
            str(saved["revision"]),
            ok=False,
        )
        self.assertIn("archive target already exists", result.stderr)
        self.assertEqual(source.read_bytes(), original)
        self.assertEqual(target.read_bytes(), sentinel)

    def test_archived_draft_is_rejected_without_task_or_archive_writes(self):
        self.invoke("status")
        self.draft("archived.json", title="Bad archive", status="archived")
        tasks_before = list((self.root / "AI_PROGRESS" / "tasks").iterdir())
        archive_before = list((self.root / "AI_PROGRESS" / "archive").iterdir())

        rejected = self.invoke("save", "--draft", "archived.json", ok=False)
        self.assertIn("use archive command", rejected.stderr)
        self.assertEqual(list((self.root / "AI_PROGRESS" / "tasks").iterdir()), tasks_before)
        self.assertEqual(list((self.root / "AI_PROGRESS" / "archive").iterdir()), archive_before)
        self.assertFalse(list((self.root / "AI_PROGRESS" / "locks").glob("*.lock")))

    def test_save_rejects_an_archived_id_without_creating_active_task(self):
        self.invoke("status")
        self.draft("original.json", title="Archived task")
        saved = self.invoke("save", "--draft", "original.json")
        self.invoke(
            "archive", saved["id"], "--expected-revision", str(saved["revision"])
        )
        archived = self.root / "AI_PROGRESS" / "archive" / f"{saved['id']}.md"
        archived_bytes = archived.read_bytes()
        active = self.root / "AI_PROGRESS" / "tasks" / f"{saved['id']}.md"
        self.assertFalse(active.exists())

        self.draft(
            "reuse.json",
            id=saved["id"],
            title="Attempt to reuse archived id",
        )
        rejected = self.invoke("save", "--draft", "reuse.json", ok=False)
        self.assertIn("already archived and cannot be reused", rejected.stderr)
        self.assertFalse(active.exists())
        self.assertEqual(archived.read_bytes(), archived_bytes)

    def test_task_folder_and_status_must_agree(self):
        self.invoke("status")

        def replace_status(path, old, new):
            original = path.read_text(encoding="utf-8")
            path.write_text(original.replace(old, new, 1), encoding="utf-8")

        self.draft("active.json", title="Active folder mismatch")
        active_saved = self.invoke("save", "--draft", "active.json")
        active = (
            self.root / "AI_PROGRESS" / "tasks" / f"{active_saved['id']}.md"
        )
        replace_status(active, "status: active", "status: archived")
        rejected_active = self.invoke("show", active_saved["id"], ok=False)
        self.assertIn("does not match tasks directory", rejected_active.stderr)

        self.draft("archive.json", title="Archive folder mismatch")
        archive_saved = self.invoke("save", "--draft", "archive.json")
        self.invoke(
            "archive", archive_saved["id"],
            "--expected-revision", str(archive_saved["revision"]),
        )
        archived = (
            self.root / "AI_PROGRESS" / "archive" / f"{archive_saved['id']}.md"
        )
        replace_status(archived, "status: archived", "status: completed")
        rejected_archive = self.invoke("show", archive_saved["id"], ok=False)
        self.assertIn("does not match archive directory", rejected_archive.stderr)
    def test_archive_unlink_failure_rolls_back_target_and_preserves_source(self):
        self.invoke("status")
        self.draft("new.json")
        saved = self.invoke("save", "--draft", "new.json")
        source = self.root / "AI_PROGRESS" / "tasks" / f"{saved['id']}.md"
        target = self.root / "AI_PROGRESS" / "archive" / f"{saved['id']}.md"
        original = source.read_bytes()
        bridge = self.load_bridge_module()
        real_unlink = Path.unlink

        def fail_source_unlink(path, *args, **kwargs):
            if path == source:
                raise OSError("injected source unlink failure")
            return real_unlink(path, *args, **kwargs)

        with mock.patch.object(Path, "unlink", new=fail_source_unlink):
            with self.assertRaises(bridge.BridgeError) as raised:
                bridge.cmd_archive(
                    self.root,
                    SimpleNamespace(
                        task=saved["id"], expected_revision=saved["revision"]
                    ),
                )
        self.assertIn("publication rolled back", str(raised.exception))
        self.assertEqual(source.read_bytes(), original)
        self.assertFalse(target.exists())

    def test_body_fields_round_trip_and_reserved_heading_is_rejected(self):
        self.invoke("status")
        values = {
            "goal": "第一行\n第二行",
            "progress": "- 完成 A\n- 完成 B\n### 細節\n可保留三級標題",
            "next_steps": "1. 測試\n2. 發布",
            "blockers": "等待回覆",
            "decisions": "採用 Markdown\n原因：可攜",
            "verification": "unit tests PASS",
            "related_files": "src/main.py\ndocs/readme.md",
            "rerun": "python -m unittest\nthen deploy",
        }
        self.draft("roundtrip.json", **values)
        saved = self.invoke("save", "--draft", "roundtrip.json")
        shown = self.invoke("show", saved["id"])
        for key, expected in values.items():
            self.assertEqual(shown[key], expected, key)

        self.draft(
            "injected.json",
            title="Injected",
            progress="safe line\n## Goal\nspoofed section",
        )
        rejected = self.invoke("save", "--draft", "injected.json", ok=False)
        self.assertIn("line beginning with ##", rejected.stderr)
        bridge = self.load_bridge_module()
        injected_path = (
            self.root / "AI_PROGRESS" / "tasks" / f"{bridge.slug('Injected')}.md"
        )
        self.assertFalse(injected_path.exists())

        self.draft(
            "carriage-return-injected.json",
            title="Carriage return injected",
            progress="safe\r## Next steps\rINJECTED",
        )
        cr_rejected = self.invoke(
            "save", "--draft", "carriage-return-injected.json", ok=False
        )
        self.assertIn("line beginning with ##", cr_rejected.stderr)
        self.assertFalse(
            (
                self.root
                / "AI_PROGRESS"
                / "tasks"
                / f"{bridge.slug('Carriage return injected')}.md"
            ).exists()
        )

    def test_malformed_utf8_is_a_single_clean_error(self):
        self.invoke("status")
        bad = self.root / "AI_PROGRESS" / "drafts" / "bad.json"
        bad.write_bytes(b"\xff\xfe\x00")
        result = self.invoke("save", "--draft", "bad.json", ok=False)
        self.assertIn("bridge error: invalid draft JSON", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(len(result.stderr.strip().splitlines()), 1)

    def test_concurrent_save_lock_prevents_double_revision(self):
        self.invoke("status")
        self.draft("new.json")
        saved = self.invoke("save", "--draft", "new.json")
        self.draft(
            "update-a.json",
            id=saved["id"],
            expected_revision=1,
            progress="writer A",
        )
        self.draft(
            "update-b.json",
            id=saved["id"],
            expected_revision=1,
            progress="writer B",
        )

        lock_path = self.root / "AI_PROGRESS" / "locks" / f"{saved['id']}.lock"
        lock_handle = lock_path.open("r+b", buffering=0)
        lock_handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        processes = [
            subprocess.Popen(
                self.command("save", "--draft", name),
                cwd=self.root.parent,
                text=True,
                encoding="utf-8",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=self.env,
            )
            for name in ("update-a.json", "update-b.json")
        ]
        try:
            time.sleep(0.5)
            self.assertTrue(all(process.poll() is None for process in processes))
        finally:
            lock_handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
            lock_handle.close()

        results = []
        for process in processes:
            stdout, stderr = process.communicate(timeout=15)
            self.assertEqual(process.returncode, 0, stderr)
            results.append(json.loads(stdout))
        self.assertEqual(
            sorted(result["result"] for result in results), ["conflict", "saved"]
        )
        self.assertEqual(self.invoke("show", saved["id"])["revision"], 2)

    def test_invalid_title_and_missing_task_fail_cleanly(self):
        self.invoke("status")
        self.draft("bad.json", title="unsafe\nstatus: completed")
        bad = self.invoke("save", "--draft", "bad.json", ok=False)
        self.assertIn("single line", bad.stderr)
        missing = self.invoke("show", "does-not-exist", ok=False)
        self.assertIn("task not found", missing.stderr)
        self.assertNotIn("Traceback", missing.stderr)

    def test_rejects_owned_symlink_or_windows_junction(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        target = self.root / "AI_PROGRESS"
        linked = False
        if hasattr(os, "symlink"):
            try:
                os.symlink(outside, target, target_is_directory=True)
                linked = True
            except OSError:
                pass
        if not linked and os.name == "nt":
            created = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(target), str(outside)],
                text=True,
                capture_output=True,
                check=False,
            )
            linked = created.returncode == 0
        if not linked:
            self.skipTest("symlink or junction unavailable")
        try:
            result = self.invoke("status", ok=False)
            self.assertIn("symlink", result.stderr.lower())
        finally:
            if target.is_symlink():
                target.unlink()
            elif target.exists():
                os.rmdir(target)


if __name__ == "__main__":
    unittest.main()
