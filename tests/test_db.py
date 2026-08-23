import pytest

import cfm.db as db


def test_schema_experiment_trial_roundtrip(tmp_path):
    conn = db.connect(tmp_path / "cfm.db")
    try:
        exp_id = db.create_experiment(
            conn, benchmark="706.stockfish_r", hostname="testhost", compiler="gcc",
            compiler_version="15.2", target_arch="znver4", budget_trials=25,
        )
        assert exp_id == 1

        trial_id = db.record_trial(
            conn, experiment_id=exp_id, phase="screening", flags=["-O3", "-flto"],
            optimize_string="-O3 -flto", build_status="ok", wspy_run_ref="testhost:run1",
            ratio=12.3, verdict="accept", ci_overlap=False,
        )
        assert trial_id == 1

        trials = db.list_trials(conn, exp_id)
        assert len(trials) == 1
        assert trials[0]["ratio"] == 12.3
        assert trials[0]["verdict"] == "accept"
        assert trials[0]["ci_overlap"] == 0

        exp = db.get_experiment(conn, exp_id)
        assert exp["benchmark"] == "706.stockfish_r"
        assert exp["status"] == "running"

        db.finish_experiment(conn, exp_id, "converged", baseline_run_ref="testhost:run0")
        exp = db.get_experiment(conn, exp_id)
        assert exp["status"] == "converged"
        assert exp["baseline_run_ref"] == "testhost:run0"
        assert exp["finished_at"] is not None
    finally:
        conn.close()


def test_update_trial_verdict_sets_verdict_delta_and_ci_overlap(tmp_path):
    conn = db.connect(tmp_path / "cfm.db")
    try:
        exp_id = db.create_experiment(conn, benchmark="x", hostname="h", compiler="gcc")
        trial_id = db.record_trial(
            conn, experiment_id=exp_id, phase="confirmation", flags=["-flto"],
            optimize_string="-flto", build_status="ok", ratio=105.0,
        )
        db.update_trial_verdict(conn, trial_id, verdict="accept", delta_vs_baseline_pct=5.0, ci_overlap=False)
        row = db.list_trials(conn, exp_id)[0]
        assert row["verdict"] == "accept"
        assert row["delta_vs_baseline_pct"] == 5.0
        assert row["ci_overlap"] == 0
    finally:
        conn.close()


def test_set_baseline_run_ref_does_not_touch_status_or_finished_at(tmp_path):
    conn = db.connect(tmp_path / "cfm.db")
    try:
        exp_id = db.create_experiment(conn, benchmark="x", hostname="h", compiler="gcc")
        db.set_baseline_run_ref(conn, exp_id, "h:run0")
        exp = db.get_experiment(conn, exp_id)
        assert exp["baseline_run_ref"] == "h:run0"
        assert exp["status"] == "running"  # unlike finish_experiment(), unaffected
        assert exp["finished_at"] is None  # ditto
    finally:
        conn.close()


def test_init_schema_is_idempotent(tmp_path):
    conn = db.connect(tmp_path / "cfm.db")
    try:
        db.init_schema(conn)  # second application must not raise
        exp_id = db.create_experiment(conn, benchmark="x", hostname="h", compiler="gcc")
        assert exp_id == 1
    finally:
        conn.close()


def test_unknown_experiment_returns_none(tmp_path):
    conn = db.connect(tmp_path / "cfm.db")
    try:
        assert db.get_experiment(conn, 999) is None
        assert db.list_trials(conn, 999) == []
    finally:
        conn.close()


def test_list_trials_by_phase_filters_correctly(tmp_path):
    conn = db.connect(tmp_path / "cfm.db")
    try:
        exp_id = db.create_experiment(conn, benchmark="x", hostname="h", compiler="gcc")
        db.record_trial(
            conn, experiment_id=exp_id, phase="screening", flags=["-flto"],
            optimize_string="-flto", build_status="ok",
        )
        db.record_trial(
            conn, experiment_id=exp_id, phase="confirmation", flags=["-flto"],
            optimize_string="-flto", build_status="ok",
        )
        db.record_trial(
            conn, experiment_id=exp_id, phase="confirmation", flags=["-flto", "-funroll-loops"],
            optimize_string="-flto -funroll-loops", build_status="ok",
        )
        screening = db.list_trials_by_phase(conn, exp_id, "screening")
        confirmation = db.list_trials_by_phase(conn, exp_id, "confirmation")
        assert len(screening) == 1
        assert len(confirmation) == 2
    finally:
        conn.close()


def test_record_hypothesis_roundtrip(tmp_path):
    conn = db.connect(tmp_path / "cfm.db")
    try:
        exp_id = db.create_experiment(conn, benchmark="x", hostname="h", compiler="gcc")
        trial_id = db.record_trial(
            conn, experiment_id=exp_id, phase="screening", flags=["-flto"],
            optimize_string="-flto", build_status="ok",
        )
        hyp_id = db.record_hypothesis(
            conn, trial_id=trial_id, proposed_by="rule",
            rationale="frontend-bound signature suggests -flto",
            evidence_json='{"resource_dominance": "frontend-bound"}', confidence=0.8,
        )
        assert hyp_id == 1
        row = conn.execute("SELECT * FROM hypotheses WHERE id=?", (hyp_id,)).fetchone()
        assert row["trial_id"] == trial_id
        assert row["proposed_by"] == "rule"
        assert row["confidence"] == 0.8
    finally:
        conn.close()


def test_upsert_knowledge_first_insert(tmp_path):
    conn = db.connect(tmp_path / "cfm.db")
    try:
        db.upsert_knowledge(
            conn, cluster_key="frontend-bound", compiler="gcc", compiler_version="15.2",
            target_arch="znver4", flag="-flto", accepted=True, delta_pct=3.5,
            last_benchmark="706.stockfish_r",
        )
        row = conn.execute(
            "SELECT * FROM knowledge WHERE cluster_key=? AND flag=?", ("frontend-bound", "-flto"),
        ).fetchone()
        assert row["n_trials"] == 1
        assert row["n_accepted"] == 1
        assert row["mean_delta_pct"] == 3.5
        assert row["stddev_delta_pct"] == 0.0
        assert row["last_benchmark"] == "706.stockfish_r"
    finally:
        conn.close()


def test_upsert_knowledge_accumulates_running_mean_and_stddev(tmp_path):
    conn = db.connect(tmp_path / "cfm.db")
    try:
        for delta, accepted, bench in [
            (10.0, True, "706.stockfish_r"),
            (20.0, True, "707.ntest_r"),
            (30.0, False, "708.sqlite_r"),
        ]:
            db.upsert_knowledge(
                conn, cluster_key="frontend-bound", compiler="gcc", compiler_version="15.2",
                target_arch="znver4", flag="-flto", accepted=accepted, delta_pct=delta,
                last_benchmark=bench,
            )
        row = conn.execute(
            "SELECT * FROM knowledge WHERE cluster_key=? AND flag=?", ("frontend-bound", "-flto"),
        ).fetchone()
        assert row["n_trials"] == 3
        assert row["n_accepted"] == 2
        # mean/sample stddev of [10, 20, 30]: mean=20, stddev=10 (n-1 denominator).
        assert row["mean_delta_pct"] == pytest.approx(20.0)
        assert row["stddev_delta_pct"] == pytest.approx(10.0)
        assert row["last_benchmark"] == "708.sqlite_r"
        # exactly one row -- the UNIQUE constraint upserted, didn't insert 3 rows.
        count = conn.execute("SELECT COUNT(*) AS n FROM knowledge").fetchone()["n"]
        assert count == 1
    finally:
        conn.close()


def test_upsert_knowledge_null_compiler_version_and_target_arch_still_upserts(tmp_path):
    # SQL's plain "=" never matches NULL against NULL -- upsert_knowledge() uses
    # "IS" specifically so a repeat call with these left unset still finds (and
    # updates) the same row rather than silently inserting a second one.
    conn = db.connect(tmp_path / "cfm.db")
    try:
        for delta in (5.0, 15.0):
            db.upsert_knowledge(
                conn, cluster_key="unknown", compiler="gcc", compiler_version=None,
                target_arch=None, flag="-funroll-loops", accepted=True, delta_pct=delta,
                last_benchmark="706.stockfish_r",
            )
        count = conn.execute("SELECT COUNT(*) AS n FROM knowledge").fetchone()["n"]
        assert count == 1
        row = conn.execute("SELECT * FROM knowledge").fetchone()
        assert row["n_trials"] == 2
        assert row["mean_delta_pct"] == pytest.approx(10.0)
    finally:
        conn.close()


def test_get_knowledge_for_cluster_orders_by_mean_delta_pct_descending(tmp_path):
    conn = db.connect(tmp_path / "cfm.db")
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
        db.upsert_knowledge(
            conn, cluster_key="memory-bound", compiler="gcc", compiler_version=None,
            target_arch=None, flag="-fprefetch-loop-arrays", accepted=False, delta_pct=3.29,
            last_benchmark="782.lbm_r",
        )

        rows = db.get_knowledge_for_cluster(conn, cluster_key="memory-bound")

        assert [r["flag"] for r in rows] == ["-march=native", "-fprefetch-loop-arrays", "-fgraphite-identity"]
        assert rows[0]["n_accepted"] == 1
        assert rows[1]["n_accepted"] == 0
    finally:
        conn.close()


def test_get_knowledge_for_cluster_scoped_to_cluster_and_compiler(tmp_path):
    conn = db.connect(tmp_path / "cfm.db")
    try:
        db.upsert_knowledge(
            conn, cluster_key="memory-bound", compiler="gcc", compiler_version=None,
            target_arch=None, flag="-march=native", accepted=True, delta_pct=48.75,
            last_benchmark="706.stockfish_r",
        )
        db.upsert_knowledge(
            conn, cluster_key="frontend-bound", compiler="gcc", compiler_version=None,
            target_arch=None, flag="-flto", accepted=True, delta_pct=6.85,
            last_benchmark="714.cpython_r",
        )

        assert [r["flag"] for r in db.get_knowledge_for_cluster(conn, cluster_key="memory-bound")] == ["-march=native"]
        assert [r["flag"] for r in db.get_knowledge_for_cluster(conn, cluster_key="frontend-bound")] == ["-flto"]
        assert db.get_knowledge_for_cluster(conn, cluster_key="compute-bound") == []
    finally:
        conn.close()


def test_get_knowledge_for_cluster_matches_null_compiler_version_and_target_arch(tmp_path):
    conn = db.connect(tmp_path / "cfm.db")
    try:
        db.upsert_knowledge(
            conn, cluster_key="memory-bound", compiler="gcc", compiler_version=None,
            target_arch=None, flag="-march=native", accepted=True, delta_pct=48.75,
            last_benchmark="706.stockfish_r",
        )
        rows = db.get_knowledge_for_cluster(
            conn, cluster_key="memory-bound", compiler_version=None, target_arch=None,
        )
        assert len(rows) == 1
    finally:
        conn.close()
