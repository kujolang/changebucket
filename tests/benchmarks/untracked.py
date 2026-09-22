#!/usr/bin/env python3
"""Offline, disposable untracked-file throughput probe (not a flaky CI gate)."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mib", type=int, default=2)
    parser.add_argument("--files", type=int, default=1)
    args = parser.parse_args()
    if args.mib < 1 or args.files < 1:
        parser.error("--mib and --files must be positive")
    kujo = os.environ.get("KUJO", "kujo")
    with tempfile.TemporaryDirectory(prefix="changebucket-benchmark-") as tmp:
        repo = Path(tmp)
        def git(*command):
            subprocess.run(["git", "-C", str(repo), *command], check=True,
                           capture_output=True)
        git("init", "-q")
        git("-c", "user.name=bench", "-c", "user.email=bench@example.invalid",
            "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
            "commit", "--allow-empty", "-qm", "baseline")
        payload = b"a line of text\n" * ((args.mib * 1024 * 1024) // 15)
        for index in range(args.files):
            (repo / f"fixture-{index}.txt").write_bytes(payload)
        started = time.perf_counter()
        result = subprocess.run([kujo, "run", str(ROOT / "changebucket.kujo"), "--",
                                 "--repo", str(repo), "--json"], text=True,
                                capture_output=True, cwd=ROOT)
        seconds = time.perf_counter() - started
        if result.returncode != 0:
            raise SystemExit(result.stdout + result.stderr)
        report = json.loads(result.stdout)
        print(json.dumps({"mib_per_file": args.mib, "files": args.files,
                          "seconds": round(seconds, 3),
                          "lines_added": report["summary"]["lines_added"]}))


if __name__ == "__main__":
    main()
