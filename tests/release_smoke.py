#!/usr/bin/env python3
"""Exercise a clean source-package layout with the installed Kujo runtime."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


SOURCE = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix="changebucket-release-smoke-") as scratch:
        root = Path(scratch)
        package = root / "changebucket"
        (package / "bin").mkdir(parents=True)
        (package / "src").mkdir()
        for name in ("changebucket.kujo", "kujo.toml", "VERSION", "LICENSE"):
            shutil.copy2(SOURCE / name, package / name)
        shutil.copy2(SOURCE / "bin/changebucket", package / "bin/changebucket")
        for module in (SOURCE / "src").glob("*.kujo"):
            shutil.copy2(module, package / "src" / module.name)
        repo = root / "user-project"
        repo.mkdir()
        subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
        (repo / "hello.kujo").write_text("print(1)\n")
        launcher = package / "bin/changebucket"
        env = dict(os.environ, KUJO=os.environ.get("KUJO", "kujo"))
        help_result = subprocess.run([str(launcher), "--help"], cwd=repo, env=env,
                                     text=True, capture_output=True, check=True)
        assert "measure the footprint" in help_result.stdout
        report = subprocess.run([str(launcher), "--json"], cwd=repo, env=env,
                                text=True, capture_output=True, check=True)
        model = json.loads(report.stdout)
        assert model["summary"]["files_added"] == 1, model
        assert model["files"][0]["path"] == "hello.kujo", model
        print("Clean package layout and launcher smoke: OK")


if __name__ == "__main__":
    main()
