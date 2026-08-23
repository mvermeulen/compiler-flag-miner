"""Knowledge agent -- doc/DESIGN.md sec. 8's cross-benchmark knowledge transfer,
M4. The write side of `cfm.db`'s ``knowledge`` table has existed since M1
(``orchestrator._confirm_flagset()``'s own upserts, gated on `phase in
("confirmation", "multiplier")`) -- this module is the first code that *reads*
it back for a new benchmark's own candidate generation, closing the loop §8
describes: "stockfish's mined flags become ntest's starting prior for free."

Scope note, matching doc/DESIGN.md sec. 15's own posture toward external data
(the reference-matrix corpus): a prior result from a *different* benchmark,
even one in the same cluster, is a hypothesis aid -- it changes which flags
get tried first and which skip Phase 3's screening trial (sec. 8 point 3) --
never a substitute measurement. Every fast-tracked flag still gets a full,
real Phase 4 confirmation-grade trial against *this* benchmark's own baseline
before anything is accepted; nothing here shortcuts the correctness gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .. import db
from ..config import CfmConfig


@dataclass
class KnownFlag:
    """One `knowledge` table row, as read back for a new benchmark's own
    candidate generation. ``has_accepted_track_record`` is what
    `cfm/orchestrator.py`'s `split_candidates_by_known_prior()` uses to decide
    which candidates skip Phase 3 screening entirely (doc/DESIGN.md sec. 8
    point 3: "a flag with a strong track record ... skips straight to Phase 4")
    -- a flag with real prior trials that were all rejected still gets
    reported (visibility into what's already known matters either way,
    doc/DESIGN.md sec. 6 Phase 4's "a documented negative result is exactly
    the kind of learning that should transfer"), just doesn't earn the
    screening skip.
    """

    flag: str
    mean_delta_pct: float
    n_trials: int
    n_accepted: int
    last_benchmark: str

    @property
    def has_accepted_track_record(self) -> bool:
        return self.n_accepted > 0


def known_flags_for_cluster(
    cfg: CfmConfig, *, cluster_key: str, compiler: str = "gcc",
    compiler_version: Optional[str] = None, target_arch: Optional[str] = None,
) -> list[KnownFlag]:
    """doc/DESIGN.md sec. 8 points 1-2, simplified for what M1/M2.5 actually
    built: the "which existing benchmarks does this one most resemble"
    clustering step (`wspy-archetype --nearest`/`--kmeans` in the original
    design) is already handled for free by `cluster_key` itself --
    `BaselineResult.resource_dominance` *is* the cluster key every
    `upsert_knowledge()` call has used since M1, a plain, consistent string
    vocabulary (`"memory-bound"`, `"frontend-bound"`, ...) shared across every
    benchmark's own characterization, not a per-run computed similarity score.
    So there's no separate discovery/lookup call needed here -- querying
    `cfm.db`'s own `knowledge` table by this benchmark's own already-
    characterized `cluster_key` directly *is* "finding the nearest existing
    benchmarks and reading their priors," just without the extra
    indirection of naming them.

    Ordered by `mean_delta_pct` descending (best-evidenced first), matching
    doc/DESIGN.md sec. 8 point 2's own ordering.
    """
    conn = db.connect(cfg.db_path)
    try:
        rows = db.get_knowledge_for_cluster(
            conn, cluster_key=cluster_key, compiler=compiler,
            compiler_version=compiler_version, target_arch=target_arch,
        )
    finally:
        conn.close()
    return [
        KnownFlag(
            flag=row["flag"], mean_delta_pct=row["mean_delta_pct"],
            n_trials=row["n_trials"], n_accepted=row["n_accepted"],
            last_benchmark=row["last_benchmark"],
        )
        for row in rows
    ]
