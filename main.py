import os
import subprocess
import shutil
import argparse

TIME_OUTPUT_FILE = "time"
BUILD_STDOUT = "stdout"
BUILD_STDERR = "stderr"
BUILD_EXIT_STATUS = "exit_status"
RESULTS = "result.csv"
DUMMY_EMAIL = "tux@tux.com"
DUMMY_NAME = "Tux"

# --------------------------------------------------------------------------

def call_cmd(cmd):
    return subprocess.run(cmd, capture_output=True, shell=True)

# --------------------------------------------------------------------------

def build(jobs=None, config=None, with_time=True):
    cmd = []

    if with_time:
        cmd = ["/usr/bin/time", "-p", "-o", TIME_OUTPUT_FILE, "--format=%e"]

    if jobs is None:
        jobs = int(subprocess.check_output("nproc"))+1

    if config is not None:
        if not os.path.isfile(config):
            raise FileNotFoundError(f"No such configuration {config}")
        if os.path.isfile(".config"):
            shutil.move(".config", ".config.old")
        shutil.copy(config, ".config")

    cmd.append("make")
    cmd.append(f"-j{jobs}")

    cmd = " ".join(cmd)
    ret = call_cmd(cmd)
    with open(BUILD_EXIT_STATUS, 'w') as status:
        status.write(str(ret.returncode))
    if ret.stdout:
        with open(BUILD_STDOUT, 'wb') as out:
            out.write(ret.stdout)
    if ret.stderr:
        with open(BUILD_STDERR, 'wb') as err:
            err.write(ret.stderr)
    return ret.returncode

# --------------------------------------------------------------------------

def build_status():
    pass

def build_is_ok():
    with open(BULID_EXIT_STATUS, 'r') as status:
        lines = status.readlines()
    return int(lines[-1]) == 0
    # return not os.path.isfile(BUILD_STDERR)

def get_build_time():
    if not os.path.isfile(TIME_OUTPUT_FILE):
        return 0
    with open(TIME_OUTPUT_FILE, 'r') as time:
        lines = time.readlines()
    return float(lines[-1])

# --------------------------------------------------------------------------

def git_init(directory="."):
    cmd = f"git init {directory}"
    return call_cmd(cmd)

def git_add_all():
    cmd = "git add -f ."
    return call_cmd(cmd)

def git_commit(msg):
    cmd = f"git commit -m \"{msg}\""
    return call_cmd(cmd)

def git_branch_list():
    cmd = "git branch -a"
    ret = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        shell=True,
        check=True)
    raw = ret.stdout.decode().split()
    return [b for b in raw if b not in {'', '*'}]

def git_branch_exists(name):
    return name in git_branch_list()

def git_create_branch(name):
    cmd = f"git checkout -b {name}"
    return call_cmd(cmd)

def git_checkout(name):
    cmd = f"git checkout '{name}'"
    return call_cmd(cmd)

def git_config(prefix, field, val):
    cmd = f"git config {prefix}.{field} \"{val}\""
    return call_cmd(cmd)

# --------------------------------------------------------------------------

def debug(msg, end="\n"):
    print(msg, end=end, flush=True)

# --------------------------------------------------------------------------

def main():

    l = ["cryptom-01", "fsm-01", "netm-01", "randm-01", "randm-02",
         "soundm-01", "driversm-01"]
    linux = "linux-5.13"
    debug(f"* Moving to {linux}")
    os.chdir(linux)

    debug("* Setting git")
    if os.path.isdir(".git"):
        debug("  - Already a git repo")
    else:
        debug("  - Initialization")
        git_init()
        debug("  - Configuration")
        git_config("user", "email", DUMMY_EMAIL)
        git_config("user", "name", DUMMY_NAME)
        debug("  - Adding everything")
        git_add_all()
        debug("  - Committing source")
        git_commit("source")

    debug("* Builds")

    for confdir in l:
        ccdir = "../{}".format(confdir)
        debug(f"* {confdir}")
        tobuild = list(
            filter(lambda x: not x.endswith("-trace"), os.listdir(ccdir)))
        tobuild.sort()
        # Clean
        for conf in tobuild:
            # git checkout master
            # git checkout -b new-branch
            # build
            # add and commit
            # git checkout master
            confpath = f"{ccdir}/{conf}"
            branch_curr = f"{confdir}-{conf}-cb"
            debug(f"  - {conf}[{branch_curr}],", end="")
            git_checkout("master")
            git_create_branch(branch_curr)
            status = build(jobs=None, config=confpath,  with_time=True)
            time = get_build_time()
            debug(f"{time}s, ok={status==0}")
            git_add_all()
            git_commit("Clean build")
        git_checkout("master")
        tobuild.remove("base")
        # Incremental
        for conf in tobuild:
            confpath = f"{ccdir}/{conf}"
            branch_curr = f"{confdir}-{conf}-ib"
            debug(f"  - {conf}[{branch_curr}],", end="")
            git_checkout(f"{confdir}-{base}-cb")
            git_create_branch(branch_curr)
            status = build(jobs=None, config=confpath,  with_time=True)
            time = get_build_time()
            debug(f"{time}s, ok={status==0}")
            git_add_all()
            git_commit("Incremental build")
        git_checkout("master")

if __name__ == "__main__":
    main()
