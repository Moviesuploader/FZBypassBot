"""Safe, manual source updater for non-container deployments.

Docker deployments should use: git pull --ff-only && docker compose up -d --build.
This script never removes .git or runs a shell command.
"""
from os import getenv
from pathlib import Path
from subprocess import run
import sys

try:
    import config
except ImportError:
    config = None

UPSTREAM_REPO = (
    getattr(config, "UPSTREAM_REPO", None) if config else None
) or getenv("UPSTREAM_REPO", "https://github.com/rjriajul/FZBypassBot")
UPSTREAM_BRANCH = (
    getattr(config, "UPSTREAM_BRANCH", None) if config else None
) or getenv("UPSTREAM_BRANCH", "main")


def main():
    if not Path(".git").is_dir():
        print("Update skipped: this directory is not a Git checkout.")
        print("For Docker, update the source on the host and rebuild the image.")
        return 2

    fetch = run(["git", "fetch", "--prune", "origin"], check=False)
    if fetch.returncode:
        print("Update failed while fetching origin.")
        return fetch.returncode

    update = run(
        ["git", "pull", "--ff-only", UPSTREAM_REPO, UPSTREAM_BRANCH],
        check=False,
    )
    if update.returncode:
        print("Update failed. Resolve local changes or branch divergence manually.")
        return update.returncode

    print("Update completed. Restart the bot process to load the new code.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
