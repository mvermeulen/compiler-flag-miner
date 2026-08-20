"""Host-exclusivity guard for mining/measurement jobs.

CLAUDE.md's "Mining jobs assume exclusive machine access" rule was, until now,
discipline only -- doc/DESIGN.md sec. 11 even said outright "this project adds no
new concurrency-control code." That held right up until it didn't: on 2026-08-20,
two ``cfm mine`` invocations launched ~13 seconds apart both reached SPECrate's
per-copy build/run fan-out around the same time, and the two runs' `stockfish_base`
copies together saturated the host's RAM -- the kernel OOM-killer thrashed for
about 90 seconds and eventually took `systemd-journald` down with it, leaving the
box needing a hard reboot. SPEC's own `lock.CPU2026` file is just a run-ID counter,
not a mutex -- it never stopped the second invocation from starting. See CLAUDE.md's
"Non-obvious traps" log for the full incident writeup.

This module is the fix: a host-wide lock any `cfm measure`/`cfm mine` invocation
must hold for its entire duration, refusing to start (not queueing, not waiting)
if another one already holds it.

Deliberately built on ``fcntl.flock()`` rather than a hand-rolled PID-file +
staleness check: the kernel releases an ``flock`` automatically when the holding
process's last file descriptor for it closes, for *any* reason -- normal exit,
an uncaught exception, or SIGKILL/being OOM-killed. That's exactly the failure
mode that caused the incident this guards against, and it means a crashed job's
lock never needs manual cleanup or a staleness heuristic to recover from -- the
next invocation just acquires it cleanly.
"""

from __future__ import annotations

import fcntl
import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

from .config import CfmConfig


class MiningLockHeld(RuntimeError):
    """Another cfm job already holds this host's mining-exclusivity lock."""


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@contextmanager
def host_lock(cfg: CfmConfig, *, command: str) -> Iterator[None]:
    """Held for the duration of one ``cfm measure``/``cfm mine`` invocation.

    Non-blocking: raises ``MiningLockHeld`` immediately if another invocation
    already holds it on this host, rather than waiting -- a mining job silently
    queued behind another is exactly the surprise this is meant to prevent, not
    a use case to accommodate.
    """
    lock_path = cfg.lock_file
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o644)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise MiningLockHeld(
                f"another cfm job already holds the mining lock ({lock_path}): "
                f"{_describe_holder(fd)}. Mining jobs assume exclusive machine "
                "access (CLAUDE.md) -- wait for it to finish before starting "
                "another."
            ) from None

        # We hold the flock now -- stamp identifying info so a *later* caller
        # that fails to acquire it can report something useful.
        os.ftruncate(fd, 0)
        os.write(fd, json.dumps({
            "pid": os.getpid(),
            "hostname": cfg.hostname,
            "command": command,
            "started_at": _utcnow_iso(),
        }).encode())
        os.fsync(fd)
        try:
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def _describe_holder(fd: int) -> str:
    """Best-effort read of the current holder's identifying info, for the error
    message only -- never load-bearing for correctness. If the holder acquired
    the flock but hasn't written its info yet, or the content is otherwise
    unreadable, fall back to a generic description rather than raise.
    """
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        info = json.loads(os.read(fd, 4096).decode())
        return (
            f"pid={info.get('pid', '?')} command={info.get('command', '?')!r} "
            f"started={info.get('started_at', '?')}"
        )
    except Exception:
        return "(unable to read lock holder details)"
