"""GDB probe that records production MuLab values for one MPI rank."""

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
RANK = int(os.environ.get("OMPI_COMM_WORLD_RANK", "0"))
REPORT_DIR = os.environ["MLVR_GDB_REPORT_DIR"]
SAMPLES: list[float] = []
FIRST_BACKTRACE: str | None = None
REPORTED = False
ENTRY_BREAKPOINT: gdb.Breakpoint | None = None


class ReturnBreakpoint(gdb.FinishBreakpoint):
    def __init__(self, mu_address: int) -> None:
        super().__init__(internal=True)
        self.mu_address = mu_address

    def stop(self) -> bool:
        global FIRST_BACKTRACE, REPORTED, ENTRY_BREAKPOINT
        value = struct.unpack("=d", bytes(gdb.selected_inferior().read_memory(self.mu_address, 8)))[0]
        SAMPLES.append(value)
        if FIRST_BACKTRACE is None:
            FIRST_BACKTRACE = gdb.execute("bt 5", to_string=True)
        if len(SAMPLES) < TARGET_COUNT:
            return False
        if not REPORTED:
            REPORTED = True
            report = {
                "rank": RANK,
                "symbol": SYMBOL,
                "mu_register": MU_REGISTER,
                "sample_count": len(SAMPLES),
                "observed_min": min(SAMPLES),
                "observed_max": max(SAMPLES),
                "mean": statistics.fmean(SAMPLES),
                "sample_sha256": hashlib.sha256(struct.pack(f"={len(SAMPLES)}d", *SAMPLES)).hexdigest(),
                "samples": SAMPLES,
                "first_backtrace": FIRST_BACKTRACE,
            }
            with open(f"{REPORT_DIR}/rank_{RANK}.json", "w", encoding="utf-8") as stream:
                json.dump(report, stream, sort_keys=True)
                stream.write("\n")
            self.enabled = False
            assert ENTRY_BREAKPOINT is not None
            ENTRY_BREAKPOINT.enabled = False
        return False


class EntryBreakpoint(gdb.Breakpoint):
    def stop(self) -> bool:
        ReturnBreakpoint(int(gdb.parse_and_eval(f"${MU_REGISTER}")))
        return False


ENTRY_BREAKPOINT = EntryBreakpoint(SYMBOL, internal=True)
gdb.execute("run")
if len(SAMPLES) < TARGET_COUNT:
    raise gdb.GdbError(f"rank {RANK} exited after {len(SAMPLES)} samples; expected {TARGET_COUNT}")
