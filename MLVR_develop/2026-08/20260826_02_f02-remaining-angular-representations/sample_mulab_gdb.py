"""GDB probe that records production `MuLab` return values."""

from __future__ import annotations

import hashlib
import json
import os
import statistics
import struct

import gdb


SYMBOL = os.environ["MLVR_GDB_SYMBOL"]
MU_REGISTER = os.environ["MLVR_GDB_MU_REGISTER"]
TARGET_COUNT = int(os.environ["MLVR_GDB_SAMPLE_COUNT"])
SAMPLES: list[float] = []
FIRST_BACKTRACE: str | None = None


class ReturnBreakpoint(gdb.FinishBreakpoint):
    def __init__(self, mu_address: int) -> None:
        super().__init__(internal=True)
        self.mu_address = mu_address

    def stop(self) -> bool:
        global FIRST_BACKTRACE
        value = struct.unpack("=d", bytes(gdb.selected_inferior().read_memory(self.mu_address, 8)))[0]
        SAMPLES.append(value)
        if FIRST_BACKTRACE is None:
            FIRST_BACKTRACE = gdb.execute("bt 5", to_string=True)
        if len(SAMPLES) < TARGET_COUNT:
            return False
        print("MLVR_MULAB_REPORT=" + json.dumps({
            "symbol": SYMBOL,
            "mu_register": MU_REGISTER,
            "sample_count": len(SAMPLES),
            "observed_min": min(SAMPLES),
            "observed_max": max(SAMPLES),
            "mean": statistics.fmean(SAMPLES),
            "sample_sha256": hashlib.sha256(struct.pack(f"={len(SAMPLES)}d", *SAMPLES)).hexdigest(),
            "samples": SAMPLES,
            "first_backtrace": FIRST_BACKTRACE,
        }, sort_keys=True), flush=True)
        return True


class EntryBreakpoint(gdb.Breakpoint):
    def stop(self) -> bool:
        ReturnBreakpoint(int(gdb.parse_and_eval(f"${MU_REGISTER}")))
        return False


EntryBreakpoint(SYMBOL, internal=True)
gdb.execute("run")
if len(SAMPLES) < TARGET_COUNT:
    raise gdb.GdbError(f"inferior exited after {len(SAMPLES)} samples; expected {TARGET_COUNT}")
