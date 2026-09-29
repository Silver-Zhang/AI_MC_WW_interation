# Artifact manifest

`artifact-manifest.sha256` paths are relative to this task directory. Verify with:

```bash
sha256sum --check logs/artifact-manifest.sha256
```

Includes task reports, harness sources, fixture inputs, all raw execution records/outputs/traces and logs. Excludes this manifest itself, Python `__pycache__`, the private source snapshot and build trees. Snapshot bytes are separately covered by `snapshot-current-sha256.txt` (paths relative to `verification/RMC-snapshot`); current and archived v1 binaries by `binary-sha256.txt` (task-relative). Build configuration, commands, flags and logs remain archived in their original locations. No raw evidence was compressed or removed.

The preliminary v1 gates/E0 and the final v2 gates/E0 are both preserved. Final E0 statistics use only v2; E1-E4 use v1. See `endpoint-metadata-amendment.md`.
