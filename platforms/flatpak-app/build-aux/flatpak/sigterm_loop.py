#!/usr/bin/env python3
"""#15581 AC: SIGTERM kolibri-daemon 0-100ms after `Kolibri running on`, N times.

Each attempt: D-Bus Start activates a fresh daemon (no app, so nothing
reactivates it), wait for a new `Kolibri running on` line, sleep 0-100ms,
SIGTERM it, then require exit within 10s and the zip-content port free.
"""

import os
import random
import signal
import socket
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import smoke_test as st  # noqa: E402

ATTEMPTS = int(os.environ.get("ATTEMPTS", "25"))


def port_free(port):
    with socket.socket() as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def wait_new_start(starts, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if st._kolibri_start_count() > starts:
            return True
        time.sleep(0.005)
    return False


def attempt(i):
    starts = st._kolibri_start_count()
    st._gdbus_call("Daemon", "/Daemon/Main", "org.learningequality.Kolibri.Daemon.Start")
    if not wait_new_start(starts, st.PHASE_WAIT_S):
        print(f"[{i}] SETUP-FAIL no new 'Kolibri running on'", flush=True)
        return None
    seen = time.monotonic()
    pids = st._daemon_pids()
    if len(pids) != 1:
        print(f"[{i}] SETUP-FAIL daemon pids {pids}", flush=True)
        return None
    (pid,) = pids
    time.sleep(random.uniform(0, 0.1))
    delay_ms = (time.monotonic() - seen) * 1000
    os.kill(pid, signal.SIGTERM)
    sent = time.monotonic()
    exited = False
    while time.monotonic() - sent < 10:
        if pid not in st._daemon_pids():
            exited = True
            break
        time.sleep(0.05)
    exit_s = time.monotonic() - sent
    free = port_free(st.ZIP_CONTENT_PORT)
    ok = exited and free
    print(
        f"[{i}] delay={delay_ms:.0f}ms exited={exited} exit_s={exit_s:.1f} "
        f"zip_port_free={free} -> {'PASS' if ok else 'FAIL'}",
        flush=True,
    )
    if not exited:
        os.kill(pid, signal.SIGKILL)
        time.sleep(1)
    return ok


def main():
    bundle = sys.argv[1]
    for argv in (
        ["flatpak", "install", "--user", "--noninteractive", "-y", "--bundle", bundle],
    ):
        st.subprocess.check_call(argv)
    st.start_environment()
    st._reset_kolibri_home()
    st._write_options()
    # First activation runs migrations; warm up so attempts time START only.
    st._wait_for(st._search_provider_answers, st.PHASE_WAIT_S)
    for pid in st._daemon_pids():
        os.kill(pid, signal.SIGKILL)
    time.sleep(2)
    results = []
    try:
        for i in range(1, ATTEMPTS + 1):
            results.append(attempt(i))
    finally:
        st.teardown()
    passed = sum(1 for r in results if r)
    failed = sum(1 for r in results if r is False)
    print(f"SUMMARY: {passed} PASS, {failed} FAIL, of {len(results)} attempts")
    return 0 if passed == ATTEMPTS else 1


if __name__ == "__main__":
    sys.exit(main())
