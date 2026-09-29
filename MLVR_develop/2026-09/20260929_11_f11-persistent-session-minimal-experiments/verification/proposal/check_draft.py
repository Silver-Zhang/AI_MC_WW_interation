#!/usr/bin/env python3
"""Read-only draft validation. Does not apply the patch, compile or run RMC."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

TASK = Path(__file__).resolve().parents[2]
ROOT = TASK.parents[2]
RMC = ROOT / 'RMC'
PATCH = TASK / 'verification/proposal/proposed-experimental.patch'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def require(condition, label):
    if not condition:
        raise AssertionError(label)
    print('PASS ' + label)

result = subprocess.run(['git', '-C', str(RMC), 'apply', '--check', str(PATCH)],
                        text=True, capture_output=True)
print('$ git -C RMC apply --check <task>/verification/proposal/proposed-experimental.patch')
print('exit_code=' + str(result.returncode))
print('stdout=' + repr(result.stdout))
print('stderr=' + repr(result.stderr))
require(result.returncode == 0, 'draft context check (no application)')

manifest = json.loads((TASK / 'verification/proposal/patch-base-manifest.json').read_text())
patch_lines = PATCH.read_text().splitlines(keepends=True)
i = 0
checked = []
while i < len(patch_lines):
    header = re.fullmatch(r'diff --git a/(\S+) b/(\S+)\n', patch_lines[i])
    require(header is not None and header[1] == header[2], 'patch file header')
    path = header[1]
    original_bytes = (RMC / path).read_bytes()
    base = original_bytes.decode().splitlines(keepends=True)
    require(sha(original_bytes) == manifest[path]['base_sha256'], path + ' base hash unchanged')
    i += 3
    pos = 0
    patched = []
    while i < len(patch_lines) and not patch_lines[i].startswith('diff --git '):
        hunk = re.fullmatch(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*\n', patch_lines[i])
        if hunk is None:
            raise AssertionError('bad hunk ' + repr(patch_lines[i]))
        start = int(hunk[1]) - 1
        assert start >= pos
        patched.extend(base[pos:start])
        pos = start
        old_count = new_count = 0
        i += 1
        while i < len(patch_lines) and not patch_lines[i].startswith(('@@ ', 'diff --git ')):
            line = patch_lines[i]
            assert line[0] in ' +-'
            if line[0] in ' -':
                assert base[pos] == line[1:], (path, pos + 1)
                pos += 1
                old_count += 1
            if line[0] in ' +':
                patched.append(line[1:])
                new_count += 1
            i += 1
        assert old_count == int(hunk[2] or 1)
        assert new_count == int(hunk[4] or 1)
    patched.extend(base[pos:])
    require(sha(''.join(patched).encode()) == manifest[path]['draft_sha256'], path + ' draft hash matches')
    off = []
    skip = False
    for line in patched:
        directive = line.strip()
        if directive in ('#ifdef RMC_F11_PROBE', '#ifdef RMC_F11_REUSE_EXPERIMENT'):
            assert not skip
            skip = True
        elif skip:
            if directive == '#endif':
                skip = False
            else:
                assert not directive.startswith('#'), 'unexpected nested conditional'
        else:
            off.append(line)
    assert not skip
    # Ignore only blank lines; all nonblank lines, including indentation, must match.
    require([s for s in off if s.strip()] == [s for s in base if s.strip()],
            path + ' default-off text matches original (blank lines ignored)')
    checked.append(path)
require(set(checked) == set(manifest) and len(checked) == 8, 'all 8 draft source files checked')

start = json.loads((TASK / 'logs/repository-state-start.json').read_text())
for relative, expected in start['protected_hashes'].items():
    require(sha((ROOT / relative).read_bytes()) == expected, relative + ' unchanged')
head = subprocess.check_output(['git', '-C', str(RMC), 'rev-parse', 'HEAD'], text=True)
status = subprocess.check_output(['git', '-C', str(RMC), 'status', '--short'], text=True)
require(head == start['git -C RMC rev-parse HEAD'], 'RMC HEAD unchanged')
require(status == start['git -C RMC status --short'], 'RMC status unchanged')
require(not (TASK / 'verification/proposal/RMC-snapshot').exists(), 'private source snapshot not created')
print('STATIC PREPARATION CHECK ONLY; compiled=false; RMC runs=0; E0-E4=BLOCKED')
