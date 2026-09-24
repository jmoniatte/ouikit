"""Commands an app runs go through here, so quitting can stop the ones still running.

Python waits for its worker threads before it exits, and each of these runs in one: without
stop_all, quitting during a slow command (a Bluetooth connect, a Wi-Fi rescan) waits for it.
BaseApp calls stop_all when the app unmounts.
"""

import subprocess
import threading

_running: set[subprocess.Popen] = set()
_lock = threading.Lock()


def run(args: list[str], timeout: float, input: str | None = None) -> subprocess.CompletedProcess:
    """Like subprocess.run with captured text output; raises FileNotFoundError and TimeoutExpired as it does."""
    process = subprocess.Popen(
        args,
        stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    with _lock:
        _running.add(process)
    try:
        stdout, stderr = process.communicate(input, timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()
        raise
    finally:
        with _lock:
            _running.discard(process)
    return subprocess.CompletedProcess(args, process.returncode, stdout, stderr)


def stop_all() -> None:
    """Kill every command still running. What it asked for may carry on elsewhere; only the wait for it ends."""
    with _lock:
        for process in _running:
            process.kill()
