"""Git utilities."""
import os
from git.repo import Repo

from knack import CLICommandsLoader
from knack.commands import CommandGroup

from easy_gpt._command import GPTCommandGroup


def _status():
    """Get the status of the git repository in the given directory."""
    git_repo = Repo.init().git
    return {"status": git_repo.status()}


class GitCommandGroup(GPTCommandGroup):
    """Git Command Group"""

    @staticmethod
    def load_command_table(loader: CLICommandsLoader) -> None:
        if os.getenv("GPT_GIT_COMMANDS"):
            with CommandGroup(loader, "git", "easy_gpt._git#{}") as group:
                group.command("status", "_status")
