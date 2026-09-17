"""GDB Python probe for production MuLab samples from a selected function."""

from __future__ import annotations

import json
import hashlib
import os
import statistics
import struct

import gdb


SYMBOL = os.environ["MLVR_GDB_SYMBOL"]
TARGET_COUNT = int(os.environ.get("MLVR_GDB_SAMPLE_COUNT", "200"))
LOWER = float(os.environ.get("MLVR_GDB_SUPPORT_LOWER", "-1.0"))
UPPER = float(os.environ.get("MLVR_GDB_SUPPORT_UPPER", "0.0"))
MU_REGISTER = os.environ.get("MLVR_GDB_MU_REGISTER", "rdx")
SAMPLES: list[float] = []
FIRST_BACKTRACE: str | None = None


class ReturnBreakpoint(gdb.FinishBreakpoint):
    def __init__(self, mu_address: int) -> None:
        super().__init__(internal=True)
        self.mu_address = mu_address

    def stop(self) -> bool:
        global FIRST_BACKTRACE
        memory = gdb.selected_inferior().read_memory(self.mu_address, 8)
        value = struct.unpack("=d", bytes(memory))[0]
        SAMPLES.append(value)
        if FIRST_BACKTRACE is None:
            FIRST_BACKTRACE = gdb.execute("bt 4", to_string=True)
        if len(SAMPLES) < TARGET_COUNT:
            return False
        violations = [sample for sample in SAMPLES if sample < LOWER or sample > UPPER]
        report = {
            "symbol": SYMBOL,
            "sample_count": len(SAMPLES),
            "expected_support": [LOWER, UPPER],
            "observed_min": min(SAMPLES),
            "observed_max": max(SAMPLES),
            "mean": statistics.fmean(SAMPLES),
            "support_violation_count": len(violations),
            "sample_sha256": hashlib.sha256(struct.pack(f"={len(SAMPLES)}d", *SAMPLES)).hexdigest(),
            "first_samples": SAMPLES[:10],
            "first_backtrace": FIRST_BACKTRACE,
        }
        print("MLVR_MULAB_REPORT=" + json.dumps(report, sort_keys=True), flush=True)
        return True


class EntryBreakpoint(gdb.Breakpoint):
    def stop(self) -> bool:
        mu_address = int(gdb.parse_and_eval(f"${MU_REGISTER}"))
        ReturnBreakpoint(mu_address)
        return False


EntryBreakpoint(SYMBOL, internal=True)
gdb.execute("run")
if len(SAMPLES) < TARGET_COUNT:
    raise gdb.GdbError(f"inferior exited after {len(SAMPLES)} samples; expected {TARGET_COUNT}")
