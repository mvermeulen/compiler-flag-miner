"""Unit tests for cfm/agents/knowledge_agent.py -- doc/DESIGN.md sec. 8's
cross-benchmark knowledge transfer, M4. Real cfm.db accessors (db.py's own
upsert_knowledge()/get_knowledge_for_cluster()), no real SPEC/wspy calls.
"""

import cfm.db as db
from cfm.agents.knowledge_agent import KnownFlag, known_flags_for_cluster
from cfm.config import CfmConfig


def _cfg(tmp_path):
    return CfmConfig.from_env(db_path=str(tmp_path / "cfm.db"))


def test_known_flags_for_cluster_returns_empty_when_nothing_known(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    conn.close()
    assert known_flags_for_cluster(cfg, cluster_key="memory-bound") == []


def test_known_flags_for_cluster_reads_real_prior_knowledge(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    try:
        db.upsert_knowledge(
            conn, cluster_key="memory-bound", compiler="gcc", compiler_version=None,
            target_arch=None, flag="-march=native", accepted=True, delta_pct=48.75,
            last_benchmark="706.stockfish_r",
        )
        db.upsert_knowledge(
            conn, cluster_key="memory-bound", compiler="gcc", compiler_version=None,
            target_arch=None, flag="-fgraphite-identity", accepted=False, delta_pct=-4.22,
            last_benchmark="706.stockfish_r",
        )
    finally:
        conn.close()

    known = known_flags_for_cluster(cfg, cluster_key="memory-bound")

    assert [k.flag for k in known] == ["-march=native", "-fgraphite-identity"]  # best-evidenced first
    assert known[0] == KnownFlag(
        flag="-march=native", mean_delta_pct=48.75, n_trials=1, n_accepted=1,
        last_benchmark="706.stockfish_r",
    )
    assert known[0].has_accepted_track_record is True
    assert known[1].has_accepted_track_record is False


def test_known_flags_for_cluster_scoped_to_the_right_cluster(tmp_path):
    cfg = _cfg(tmp_path)
    conn = db.connect(cfg.db_path)
    try:
        db.upsert_knowledge(
            conn, cluster_key="frontend-bound", compiler="gcc", compiler_version=None,
            target_arch=None, flag="-flto", accepted=True, delta_pct=6.85,
            last_benchmark="714.cpython_r",
        )
    finally:
        conn.close()

    assert known_flags_for_cluster(cfg, cluster_key="memory-bound") == []
    assert [k.flag for k in known_flags_for_cluster(cfg, cluster_key="frontend-bound")] == ["-flto"]
