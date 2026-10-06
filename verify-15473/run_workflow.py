#!/usr/bin/env python3
"""Run deploy_pages.yml's job on this runner against a locally served site.

usage: run_workflow.py <workflow.yml> <served-site-dir>

`${{ }}` values in `env:` must already be in the environment (SITE_URL,
DEB_URL, DEBIAN_REPO_SIGNING_KEY). upload-pages-artifact + deploy-pages are
simulated by replacing the served directory's contents with the artifact.
Exit 0 on success; on failure prints FAILED_STEP=<name> and exits 1.
"""
import os
import shutil
import subprocess
import sys
import tempfile

import yaml


def resolve(mapping):
    out = {}
    for key, value in (mapping or {}).items():
        value = str(value)
        if "${{" in value:
            if key not in os.environ:
                sys.exit(f"harness: {key} must be set in the environment")
            value = os.environ[key]
        out[key] = value
    return out


def deploy(artifact, site):
    for name in os.listdir(site):
        path = os.path.join(site, name)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    shutil.copytree(artifact, site, dirs_exist_ok=True)


def main(workflow, site):
    site = os.path.abspath(site)
    with open(workflow) as f:
        job = next(iter(yaml.safe_load(f)["jobs"].values()))
    workdir = tempfile.mkdtemp(prefix="workspace-")
    runner_temp = tempfile.mkdtemp(prefix="runner-temp-")
    env = dict(os.environ, RUNNER_TEMP=runner_temp, GITHUB_WORKSPACE=workdir)
    env.update(resolve(job.get("env")))
    artifact = None
    for step in job["steps"]:
        name = step.get("name") or step.get("uses")
        print(f"::group::{name}", flush=True)
        if "if" in step:
            sys.exit(f"harness: step {name!r} has an if:, unsupported")
        if "uses" in step:
            action = step["uses"].split("@")[0]
            if action == "actions/upload-pages-artifact":
                artifact = os.path.join(workdir, step["with"]["path"])
            elif action == "actions/deploy-pages":
                if not os.path.isdir(artifact or ""):
                    print("::endgroup::", flush=True)
                    print(f"FAILED_STEP={name}", flush=True)
                    return 1
                deploy(artifact, site)
            else:
                sys.exit(f"harness: unsupported action {action}")
            print("::endgroup::", flush=True)
            continue
        if "${{" in step["run"]:
            sys.exit(f"harness: step {name!r} has ${{{{ }}}} inside run:")
        github_env = os.path.join(runner_temp, "github_env")
        open(github_env, "w").close()
        step_env = dict(env, GITHUB_ENV=github_env, GITHUB_OUTPUT=os.devnull)
        step_env.update(resolve(step.get("env")))
        result = subprocess.run(
            ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", step["run"]],
            cwd=workdir,
            env=step_env,
        )
        print("::endgroup::", flush=True)
        if result.returncode != 0:
            print(f"FAILED_STEP={name}", flush=True)
            return 1
        with open(github_env) as f:
            for line in f:
                key, _, value = line.rstrip("\n").partition("=")
                env[key] = value
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
