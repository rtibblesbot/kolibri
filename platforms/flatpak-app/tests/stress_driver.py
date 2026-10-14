import os
import subprocess
import sys

RUNS = 80
TAKEN = "test_run_fails_when_bus_name_is_taken"

conf = sys.argv[1]
os.sched_setaffinity(0, {0})


def start(*names):
    return subprocess.Popen(
        ["dbus-run-session", "--config-file", conf, "--", sys.executable, "-m", "unittest", "-v", *names],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def failed_tests(output):
    return sorted(
        line.split()[1]
        for line in output.splitlines()
        if line.startswith(("FAIL: ", "ERROR: "))
    )


primary_taken = 0
second_taken = 0
primary_failing_runs = 0
other = {}
for i in range(RUNS):
    a = start()
    b = start()
    out_a, _ = a.communicate()
    out_b, _ = b.communicate()
    fa = failed_tests(out_a)
    fb = failed_tests(out_b)
    if a.returncode:
        primary_failing_runs += 1
    primary_taken += TAKEN in fa
    second_taken += TAKEN in fb
    for name in fa + fb:
        other[name] = other.get(name, 0) + 1
    print(f"run {i + 1}: primary rc={a.returncode} {fa} second rc={b.returncode} {fb}", flush=True)
    if i == 0:
        print(out_a, flush=True)

alone = start(f"test_application.TestApplication.{TAKEN}")
out_alone, _ = alone.communicate()
print(out_alone)

summary = (
    f"cpus={os.sched_getaffinity(0)} runs={RUNS} "
    f"primary_{TAKEN}_failures={primary_taken} primary_failing_runs={primary_failing_runs} "
    f"second_copy_{TAKEN}_failures={second_taken} all_failures={other} "
    f"alone_rc={alone.returncode}"
)
print(f"::warning title=stress-15580::{summary}", flush=True)
sys.exit(1 if primary_taken or second_taken or alone.returncode else 0)
