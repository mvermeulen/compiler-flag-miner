import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from cfm.config import CfmConfig
from cfm.lock import MiningLockHeld, host_lock


def _cfg(tmp_path: Path) -> CfmConfig:
    return CfmConfig.from_env(lock_file=str(tmp_path / "test.lock"))


def test_host_lock_acquires_and_releases(tmp_path):
    cfg = _cfg(tmp_path)
    with host_lock(cfg, command="cfm measure 706.stockfish_r"):
        pass
    # Released on clean exit -- a second acquisition afterwards must succeed.
    with host_lock(cfg, command="cfm measure 706.stockfish_r"):
        pass


def test_host_lock_refuses_concurrent_acquisition(tmp_path):
    cfg = _cfg(tmp_path)
    with host_lock(cfg, command="cfm mine 706.stockfish_r"):
        with pytest.raises(MiningLockHeld) as exc_info:
            with host_lock(cfg, command="cfm mine 999.other_r"):
                pass
    assert "cfm mine 706.stockfish_r" in str(exc_info.value)
    assert str(os.getpid()) in str(exc_info.value)


def test_host_lock_released_even_on_exception(tmp_path):
    cfg = _cfg(tmp_path)
    with pytest.raises(RuntimeError, match="boom"):
        with host_lock(cfg, command="cfm mine 706.stockfish_r"):
            raise RuntimeError("boom")
    # A prior holder that raised must still have released the lock.
    with host_lock(cfg, command="cfm mine 706.stockfish_r"):
        pass


def test_host_lock_creates_parent_directory(tmp_path):
    nested = tmp_path / "does" / "not" / "exist" / "test.lock"
    cfg = CfmConfig.from_env(lock_file=str(nested))
    with host_lock(cfg, command="cfm mine 706.stockfish_r"):
        assert nested.exists()


def test_host_lock_auto_released_when_holder_is_killed(tmp_path):
    """The whole point of using flock over a hand-rolled PID file: the kernel
    releases the lock when the holding process dies for *any* reason, including
    a hard kill -- exactly the OOM-kill/crash scenario this guard exists for
    (see cfm/lock.py's module docstring). No manual staleness check needed.
    """
    lock_path = tmp_path / "test.lock"
    holder = subprocess.Popen(
        [
            sys.executable, "-c",
            "from cfm.config import CfmConfig\n"
            "from cfm.lock import host_lock\n"
            f"cfg = CfmConfig.from_env(lock_file={str(lock_path)!r})\n"
            "with host_lock(cfg, command='cfm mine 706.stockfish_r'):\n"
            "    print('locked', flush=True)\n"
            "    import time; time.sleep(60)\n"
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        line = holder.stdout.readline()
        assert line.strip() == "locked"

        cfg = _cfg(tmp_path)
        with pytest.raises(MiningLockHeld):
            with host_lock(cfg, command="cfm mine 999.other_r"):
                pass

        holder.send_signal(signal.SIGKILL)
        holder.wait(timeout=5)

        # Give the kernel a moment to tear down the dead process's fds; then
        # the lock must be immediately acquirable, with no cleanup needed.
        deadline = time.time() + 5
        last_error = None
        while time.time() < deadline:
            try:
                with host_lock(cfg, command="cfm mine 999.other_r"):
                    return
            except MiningLockHeld as exc:
                last_error = exc
                time.sleep(0.1)
        raise AssertionError(f"lock never became available after holder was killed: {last_error}")
    finally:
        if holder.poll() is None:
            holder.kill()
            holder.wait()
