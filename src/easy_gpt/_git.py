"""Git utilities."""
from git import Repo


def _status():
    """Get the status of the git repository in the given directory."""
    git_repo = Repo.init().git
    return {"status": git_repo.status()}
