"""
python3 create_worker.py ABQ77UXII2RYNXGMOFKDOBLEDCOZS --gh_label "a100" --gh_url https://github.com/fairinternal/xformers --gres=gpu:1 --partition=a100 --time=3-0
"""
import os
import subprocess
import argparse
import shutil
import shlex

LAYOUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "_layout"))
WORKERS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "_workers"))


# Setup worker
def _setup_worker(token: str, label: str, gh_url: str) -> str:
    reponame = gh_url.split('/')[-1]
    org = gh_url.split('/')[-2]
    name = f"{org}_{reponame}_{label}_{token[:4]}"
    worker_dir = os.path.join(WORKERS_DIR, name)
    os.makedirs(WORKERS_DIR, exist_ok=True)
    if os.path.isdir(worker_dir):
        print("worker already created - returning")
        return worker_dir
    
    worker_dir_tmp = f"{worker_dir}_tmp"
    print(f"Creating worker in: {worker_dir_tmp}")
    os.makedirs(worker_dir_tmp, exist_ok=False)
    for path in [
        "bin", "externals"
    ]:
        print("* Copy", path)
        shutil.copytree(os.path.join(LAYOUT_DIR, path), os.path.join(worker_dir_tmp, path))

    subprocess.check_call([
        os.path.join(worker_dir_tmp, "bin", "Runner.Listener"),
        "configure",
        "--unattended",
        "--token", token,
        "--url", gh_url,
        "--name", name,
        "--labels", str(label),
        "--work", "_work",
    ], cwd=worker_dir_tmp)
    os.rename(worker_dir_tmp, worker_dir)
    return worker_dir

def _exec(args):
    print("EXEC: ", shlex.join(args))
    subprocess.check_call(args)

parser = argparse.ArgumentParser()
parser.add_argument("runner_setup_token", help="Token obtained on `bunnylol oss` tool")
parser.add_argument("--gh_label", help="Label for 'runs-on:' field in ghaction config")
parser.add_argument("--gh_url", help="GitHub repo URL")
args, remained = parser.parse_known_args()


worker_dir = _setup_worker(args.runner_setup_token, label=args.gh_label, gh_url=args.gh_url)
print(f"Worker available: {worker_dir}")

# Run worker
run_worker_cmd = [
    "singularity", "run",
    "--no-home",
    "--bind", f"{worker_dir}:/ghrunner",
    "sandbox/",
    "/ghrunner/bin/Runner.Listener", "run"
]
run_worker_cmd_on_slurm = [
    "srun",
    *remained,
    *run_worker_cmd
]
while True:
    # Run locally
    os.environ["RUNNER_KILL_ON_JOB"] = "1"
    try:
        _exec(run_worker_cmd)
    except subprocess.CalledProcessError as e:
        assert e.returncode == 1

    # We got a job - re-run on Slurm to execute it
    # We expect the runner to then shutdown once it's
    # done executing jobs
    del os.environ["RUNNER_KILL_ON_JOB"]
    try:
        _exec(run_worker_cmd_on_slurm)
    except subprocess.CalledProcessError as e:
        assert e.returncode == 1