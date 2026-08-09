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
