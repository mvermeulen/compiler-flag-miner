"""Memory-bandwidth probe and pre-trial gate.

On niwot (doc/lbm_swing_investigation.2026-10-23.md) the memory side throttles
under sustained bandwidth load: a 16-thread triad drops from about 45 to about
22.5 GB/s, and 782.lbm_r's ratio for the same -O3 binary ranges from 6.33 down to
3.02. The throttle lets go within about 30 seconds of idle. The cause isn't known
(not the power profile, core clocks or page placement), so this works around it
instead: before each timed run, probe bandwidth, and wait while it reads well
below the best seen this session.

The probe is a small OpenMP triad (``_TRIAD_SRC``), compiled once with the host's
``gcc`` into ``<output_root>/.cache/``. Every failure degrades to ``None`` and the
gate then lets the trial through: a missing compiler or a failed probe must never
block a mining run.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

# A probe below this fraction of the session's best reading counts as throttled.
# niwot's two states are about 45 and 22.5 GB/s; fast-state probes vary by a few
# percent.
GATE_FRACTION = 0.85
# While throttled: idle this long between probes, for at most MAX_WAIT_S in all.
# niwot recovered within 32 s of idle.
PROBE_INTERVAL_S = 30.0
MAX_WAIT_S = 300.0

# Three 512 MB arrays, 50 triad passes: a few seconds of load, well past every
# cache level on current client parts.
_TRIAD_SRC = r"""
#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#define N (64L*1024*1024)
int main(void){
  double *a=malloc(N*8),*b=malloc(N*8),*c=malloc(N*8),sum=0;
  if(!a||!b||!c) return 1;
  #pragma omp parallel for
  for(long i=0;i<N;i++){a[i]=1;b[i]=2;c[i]=0;}
  for(int r=0;r<50;r++){
    double t=omp_get_wtime();
    #pragma omp parallel for
    for(long i=0;i<N;i++) c[i]=a[i]+3.0*b[i];
    sum+=3.0*N*8/(omp_get_wtime()-t)/1e9;
  }
  printf("%.2f %g\n",sum/50,c[N/2]);
  return 0;
}
"""


def _probe_binary(cache_dir: Path) -> Optional[Path]:
    digest = hashlib.sha256(_TRIAD_SRC.encode()).hexdigest()[:12]
    binary = cache_dir / f"triad-{digest}"
    if binary.exists():
        return binary
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        src = cache_dir / f"triad-{digest}.c"
        src.write_text(_TRIAD_SRC)
        subprocess.run(
            ["gcc", "-O3", "-fopenmp", str(src), "-o", str(binary)],
            check=True, capture_output=True, timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return binary if binary.exists() else None


def probe_gbps(cache_dir: Path) -> Optional[float]:
    """Mean triad bandwidth in GB/s over every hardware thread, or None if the
    probe couldn't be built or run."""
    binary = _probe_binary(cache_dir)
    if binary is None:
        return None
    env = dict(os.environ, OMP_NUM_THREADS=str(os.cpu_count() or 1))
    try:
        out = subprocess.run(
            [str(binary)], check=True, capture_output=True, text=True, timeout=120, env=env,
        ).stdout
        return float(out.split()[0])
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        return None


@dataclass
class GateResult:
    probe_gbps: Optional[float]   # the last probe before the run (None: probe unavailable)
    best_gbps: Optional[float]    # the session's best reading, including this wait
    waited_s: float
    passed: bool                  # False only when MAX_WAIT_S ran out still throttled

    def rationale(self) -> str:
        if self.probe_gbps is None:
            return "memory bandwidth probe before run: unavailable"
        text = (
            f"memory bandwidth probe before run: {self.probe_gbps:.1f} GB/s "
            f"(session best {self.best_gbps:.1f}, waited {self.waited_s:.0f} s)"
        )
        if not self.passed:
            text += (
                f" -- WARNING: still below {GATE_FRACTION:.0%} of the session best after "
                f"{MAX_WAIT_S:.0f} s; ran anyway"
            )
        return text


class BandwidthGate:
    """Holds the session's best probe reading across trials. ``probe`` and
    ``sleep`` are injectable so the waiting logic is testable without load or
    real time."""

    def __init__(
        self,
        cache_dir: Path,
        *,
        probe: Optional[Callable[[], Optional[float]]] = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._probe = probe or (lambda: probe_gbps(cache_dir))
        self._sleep = sleep
        self.best: Optional[float] = None

    def _read(self) -> Optional[float]:
        value = self._probe()
        if value is not None and (self.best is None or value > self.best):
            self.best = value
        return value

    def wait(self) -> GateResult:
        """Probes until bandwidth reads at least ``GATE_FRACTION`` of the session
        best, idling ``PROBE_INTERVAL_S`` between probes, for at most
        ``MAX_WAIT_S``. The very first call always probes twice, so a session
        that starts throttled doesn't take a throttled reading as its best."""
        first_call = self.best is None
        value = self._read()
        if value is None:
            return GateResult(probe_gbps=None, best_gbps=None, waited_s=0.0, passed=True)
        waited = 0.0
        if first_call:
            self._sleep(PROBE_INTERVAL_S)
            waited += PROBE_INTERVAL_S
            value = self._read() or value
        while value < GATE_FRACTION * self.best:
            if waited >= MAX_WAIT_S:
                return GateResult(probe_gbps=value, best_gbps=self.best, waited_s=waited, passed=False)
            self._sleep(PROBE_INTERVAL_S)
            waited += PROBE_INTERVAL_S
            value = self._read() or value
        return GateResult(probe_gbps=value, best_gbps=self.best, waited_s=waited, passed=True)
