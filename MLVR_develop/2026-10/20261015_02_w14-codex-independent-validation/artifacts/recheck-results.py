#!/usr/bin/env python3
"""Recheck archived numerical results; no RMC build/run or evidence mutation."""
from pathlib import Path
import json
import shutil
import subprocess
import tempfile


def main():
    task = Path(__file__).resolve().parents[1]
    evidence = task / "logs/local-evidence"
    if not (evidence / "cases.json").is_file():
        raise SystemExit("Missing local raw evidence: " + str(evidence))
    with tempfile.TemporaryDirectory(prefix="w14-archive-recheck-") as temporary:
        work = Path(temporary)
        for relative in ["cases.json", "logs/mgace-groups.json"]:
            target = work / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(evidence / relative, target)
        cases = json.loads((work / "cases.json").read_text())
        for case in cases:
            for name in ["events.jsonl", "inp.out"]:
                relative = Path("runs/gdb-final") / case["name"] / name
                target = work / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(evidence / relative, target)
        source = (task / "artifacts/scripts/analyze.py").read_text()
        old = "P=Path('/tmp/w14-codex-review');"
        if source.count(old) != 1:
            raise SystemExit("Unexpected historical analysis root declaration")
        source = source.replace(old, "P=Path(" + repr(str(work)) + ");")
        result = subprocess.run(["python3", "-c", source], cwd=work, capture_output=True, text=True)
        if result.returncode:
            raise SystemExit(result.stdout + result.stderr)
        for name in ["results.json", "results-table.md"]:
            if (work / name).read_bytes() != (evidence / name).read_bytes():
                raise SystemExit("Archived analysis mismatch: " + name)
            print(name + ": byte-identical")
        print(str(len(cases)) + " cases rechecked from persistent evidence; no RMC execution")


if __name__ == "__main__":
    main()
