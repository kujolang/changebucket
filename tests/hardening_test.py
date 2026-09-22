#!/usr/bin/env python3
"""Public CLI regressions using only Python's standard library and local Git."""
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
GIT = shutil.which("git")
KUJO = os.environ.get("KUJO", "kujo")


class Hardening(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="changebucket-hardening-")
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.repo = self.work / "repo ' with spaces"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.hooksPath", "/dev/null")
        (self.repo / "seed").write_text("one\n")
        self.git("add", "seed")
        self.git("commit", "-qm", "seed")

    def git(self, *args):
        return subprocess.run([GIT, "-C", str(self.repo), *args],
                              check=True, capture_output=True, text=True).stdout

    def cli(self, *args, code=0, env=None):
        prefix = ["check"] if args and args[0] == "check" else []
        options = args[1:] if prefix else args
        result = subprocess.run([KUJO, "run", str(ROOT / "changebucket.kujo"),
                                 "--", *prefix, "--repo", str(self.repo), *options],
                                capture_output=True, text=True, env=env, cwd=ROOT)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result.stdout

    def wrapper_env(self, failure=""):
        wrapper = self.work / "git"
        wrapper.write_text("#!/bin/sh\n"
                           'printf "%s\\n" "$*" >> "$CB_LOG"\n'
                           'case "$*" in\n'
                           '  *"$CB_FAIL"*) if [ -n "$CB_FAIL" ]; then '
                           'echo "injected git failure" >&2; exit 19; fi;;\n'
                           'esac\n'
                           f"exec {shlex.quote(GIT)} \"$@\"\n")
        wrapper.chmod(0o700)
        return dict(os.environ, PATH=str(self.work) + os.pathsep + os.environ["PATH"],
                    CB_LOG=str(self.work / "calls"), CB_FAIL=failure)

    def test_git_failures_are_not_empty_success(self):
        for failure in ("--show-toplevel", "--verify", "--name-status", "--numstat", "ls-files"):
            with self.subTest(failure=failure):
                output = self.cli("--json", env=self.wrapper_env(failure), code=1)
                self.assertIn("injected git failure", output)
                self.assertTrue(output.startswith("error:"))

    def test_truncated_capture_fails_before_parsing(self):
        wrapper = self.work / "git"
        wrapper.write_text(f"#!{sys.executable}\nimport os, sys\n"
                           'if "--numstat" in sys.argv:\n'
                           '    sys.stdout.write("x" * (16777216 + 1))\n'
                           '    sys.exit(0)\n'
                           f'os.execv({GIT!r}, [{GIT!r}] + sys.argv[1:])\n')
        wrapper.chmod(0o700)
        env = dict(os.environ, PATH=str(self.work) + os.pathsep + os.environ["PATH"])
        self.assertIn("capture limit", self.cli("--json", env=env, code=1))

    def test_git_process_count_and_read_only_boundary(self):
        self.cli("--json", env=self.wrapper_env())
        calls = (self.work / "calls").read_text().splitlines()
        self.assertEqual(len(calls), 6, calls)
        self.assertEqual(sum(" diff " in c for c in calls), 2)
        for call in calls:
            self.assertTrue(any(command in call for command in
                                (" rev-parse ", " diff ", " ls-files ")), call)

    def test_ref_path_collision_and_empty_value(self):
        (self.repo / "HEAD").write_text("path\n")
        model = json.loads(self.cli("--base", "HEAD", "--json"))
        self.assertEqual(model["summary"]["files_added"], 1)
        (self.repo / "not-a-ref").write_text("path\n")
        self.cli("--base", "not-a-ref", code=1)
        for flag in ("--base", "--head", "--repo", "--output"):
            self.assertIn("missing value", self.cli(flag, "", code=2))

    def test_dangling_and_binary_named_symlinks(self):
        (self.repo / "missing.js").symlink_to("absent")
        (self.repo / "link.png").symlink_to("seed")
        files = json.loads(self.cli("--json"))["files"]
        self.assertEqual(len(files), 2)
        for entry in files:
            self.assertEqual(entry["additions"], 1)
            self.assertFalse(entry["binary"])

    def test_untracked_content_probe_and_no_symlink_target_read(self):
        (self.repo / "unknown.data").write_bytes(b"plain\x00binary\n")
        (self.repo / "legacy.data").write_bytes(b"\xff\n")
        outside = self.work / "external.data"
        outside.write_bytes(b"secret\x00outside\n")
        (self.repo / "external.data").symlink_to(outside)
        files = {entry["path"]: entry for entry in json.loads(self.cli("--json"))["files"]}
        self.assertTrue(files["unknown.data"]["binary"])
        self.assertEqual(files["unknown.data"]["additions"], 0)
        self.assertEqual(files["legacy.data"]["additions"], 1)
        self.assertFalse(files["external.data"]["binary"])
        self.assertEqual(files["external.data"]["additions"], 1)

    def test_large_untracked_stream_and_chunk_boundary(self):
        (self.repo / "boundary.txt").write_bytes(b"a" * 65535 + b"\nb")
        (self.repo / "large.txt").write_bytes(b"line\n" * 3600000)
        files = {entry["path"]: entry for entry in json.loads(self.cli("--json"))["files"]}
        self.assertEqual(files["boundary.txt"]["additions"], 2)
        self.assertEqual(files["large.txt"]["additions"], 3600000)

    def test_hostile_paths_stay_data(self):
        name = "é-escape\x1b[31m\x07|`'$.js"
        (self.repo / name).write_text("one\ntwo")
        model = json.loads(self.cli("--json"))
        self.assertEqual(model["files"][0]["path"], name)
        self.assertEqual(model["files"][0]["additions"], 2)
        for args in ((), ("--markdown",)):
            output = self.cli(*args)
            self.assertNotIn("\x1b", output)
            self.assertNotIn("\x07", output)
            self.assertIn("\\u001b", output)

    def test_git_configuration_does_not_hide_changes(self):
        self.git("config", "diff.relative", "true")
        self.git("config", "diff.external", "false")
        (self.repo / "seed").write_text("two\n")
        model = json.loads(self.cli("--json"))
        self.assertEqual(model["summary"]["total_churn"], 2)

    def test_modern_dependency_budget(self):
        for name, ban, category in (("uv.lock", "--no-lockfile-changes", "lockfiles"),
                                    ("deno.json", "--no-dependency-changes", "dependency_manifests")):
            with self.subTest(name=name):
                path = self.repo / name
                path.write_text("one\n")
                model = json.loads(self.cli("--json"))
                self.assertIn(name, model["categories"][category])
                self.assertFalse(json.loads(self.cli("check", ban, "--json", code=1))["budget"]["passed"])
                path.unlink()

    def test_category_corpus_from_real_kujo_repositories(self):
        cases = json.loads((ROOT / "tests/fixtures/category_cases.json").read_text())
        for case in cases:
            path = self.repo / case["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("example\n")
        files = {entry["path"]: entry for entry in json.loads(self.cli("--json"))["files"]}
        for case in cases:
            with self.subTest(path=case["path"]):
                self.assertEqual(files[case["path"]]["categories"], case["categories"])

    def test_markdown_budget_messages_are_literal(self):
        (self.repo / "dist").mkdir()
        name = "<img src=x>_[link](url).js"
        (self.repo / "dist" / name).write_text("one\n")
        output = self.cli("--markdown", "--no-generated-changes")
        budget = output.split("## Budget Result")[1].split("## File Categories")[0]
        self.assertNotIn("<img", budget)
        self.assertNotIn("[link]", budget)
        self.assertIn("&lt;img", budget)

    def test_root_with_trailing_carriage_return(self):
        renamed = self.repo.with_name("repo\r")
        self.repo.rename(renamed)
        self.repo = renamed
        (self.repo / "new.js").write_text("one\n")
        self.assertEqual(json.loads(self.cli("--json"))["summary"]["lines_added"], 1)

    def test_numeric_leading_zeroes(self):
        zeros = "0" * 40
        self.cli("--max-files", zeros + "1", "--json")
        self.cli("--max-files", zeros + "9223372036854775808", code=2)

    def test_output_is_atomic_and_conflicts_are_explicit(self):
        report = self.work / "report.md"
        outside = self.work / "important.txt"
        outside.write_text("keep me\n")
        report.symlink_to(outside)
        self.cli("--output", str(report))
        self.assertTrue(report.is_file())
        self.assertFalse(report.is_symlink())
        self.assertTrue(report.read_text().startswith("# ChangeBucket Report"))
        self.assertEqual(outside.read_text(), "keep me\n")
        for args in (("--json", "--markdown"), ("--json", "--output", str(report))):
            with self.subTest(args=args):
                self.assertIn("cannot be combined", self.cli(*args, code=2))
        self.assertTrue(report.read_text().startswith("# ChangeBucket Report"))
        missing = self.work / "missing" / "report.md"
        self.assertIn("could not write report", self.cli("--output", str(missing), code=1))
        self.assertFalse(missing.exists())

    def test_opt_in_rename_and_directory_v2_contract(self):
        (self.repo / "folder").mkdir()
        target = "folder/new\tline\n.js"
        self.git("mv", "seed", target)
        original = json.loads(self.cli("--json"))
        self.assertNotIn("schema_version", original)
        self.assertEqual(original["summary"]["files_deleted"], 1)
        model = json.loads(self.cli("--detect-renames", "--by-directory", "--json"))
        self.assertEqual(model["schema_version"], 2)
        self.assertEqual(model["summary"]["files_changed"], 1)
        self.assertEqual(model["summary"]["files_renamed"], 1)
        self.assertEqual(model["summary"]["files_deleted"], 0)
        self.assertEqual(model["files"][0]["previous_path"], "seed")
        self.assertEqual(model["files"][0]["path"], target)
        self.assertEqual(model["directories"]["folder/"]["files_changed"], 1)
        self.assertEqual(model["directories"]["folder/"]["total_churn"], 0)
        budget = json.loads(self.cli("check", "--detect-renames", "--no-deletes",
                                     "--json"))
        self.assertTrue(budget["budget"]["passed"])
        self.assertIn("Top-level directories", self.cli("--detect-renames", "--by-directory"))
        self.assertIn("## Top-level Directories", self.cli("--by-directory", "--markdown"))

    def test_large_pure_move_preserves_zero_churn(self):
        (self.repo / "original.txt").write_bytes(b"different line\n" * 140000)
        self.git("add", "original.txt")
        self.git("commit", "-qm", "large fixture")
        (self.repo / "subdir").mkdir()
        self.git("mv", "original.txt", "subdir/moved.txt")
        model = json.loads(self.cli("--detect-renames", "--by-directory", "--json"))
        self.assertEqual(model["summary"]["files_renamed"], 1)
        self.assertEqual(model["summary"]["total_churn"], 0)
        self.assertEqual(model["files"][0]["previous_path"], "original.txt")
        self.assertEqual(model["directories"]["subdir/"]["total_churn"], 0)

    def test_unborn_object_formats(self):
        for object_format in ("sha1", "sha256"):
            self.repo = self.work / object_format
            self.repo.mkdir()
            self.git("init", "-q", "--object-format=" + object_format)
            (self.repo / "new.js").write_text("new\n")
            self.git("add", "new.js")
            model = json.loads(self.cli("--json"))
            self.assertEqual(model["base"], "(empty tree)")
            self.assertEqual(model["summary"]["lines_added"], 1)

    def test_untracked_read_failure_is_not_zero_churn(self):
        for name in ("vanished.js", "vanished.png"):
            with self.subTest(name=name):
                wrapper = self.work / "git"
                wrapper.write_text('#!/bin/sh\ncase "$*" in\n'
                                   f'*ls-files*) printf "{name}\\000"; exit 0;;\nesac\n'
                                   f'exec {shlex.quote(GIT)} "$@"\n')
                wrapper.chmod(0o700)
                env = dict(os.environ, PATH=str(self.work) + os.pathsep + os.environ["PATH"])
                self.assertIn("cannot read untracked file", self.cli("--json", env=env, code=1))


if __name__ == "__main__":
    unittest.main()
