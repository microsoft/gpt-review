"""Basic Shell Commands for Git."""
import logging
import subprocess

from simple_gpt.report import process_yaml


def _diff_sh() -> str:
    """
    Get the diff of the PR
    - run git commands via python
    """
    return subprocess.run(
        ["git", "--no-pager", "diff", "--cached"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    ).stdout.decode("utf-8")


def _commit_message(args) -> str:
    """Commit the changes."""

    if len(args.input_args) == 3:
        with open(args.input_args[2], encoding="utf8") as yaml_config:
            return process_yaml(_diff_sh(), yaml_config, headers=False)

    yaml_config = """
report:
    _: Create a short git commit message for these changes
"""
    return process_yaml(_diff_sh(), yaml_config, headers=False)


def _commit_sh(message: str) -> str:
    return subprocess.run(
        ["git", "commit", "-m", f"{message}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    ).stdout.decode("utf-8")


def _commit(args) -> str:
    """
    Commit the changes.

    Args:
        args (argparse.Namespace): The arguments.

    Returns:
        str: The output of the git commit command.
    """

    commit_message = _commit_message(args)
    logging.info("Diff: %s", commit_message)
    return _commit_sh(commit_message)


def _push_sh(args) -> str:
    """
    Push changes.

    Args:
        args (argparse.Namespace): The arguments.

    Returns:
        str: The output of the git push command.
    """
    repository = "origin" if len(args.input_args) <= 2 else args.input_args[2]
    refspec = "HEAD" if len(args.input_args) <= 2 else args.input_args[3]
    return subprocess.run(
        ["git", "push", repository, refspec],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    ).stdout.decode("utf-8")


def _pull_sh(args) -> str:
    """
    Pull changes.

    Args:
        args (argparse.Namespace): The arguments.

    Returns:
        str: The output of the git pull command.
    """
    return subprocess.run(
        ["git", "pull"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    ).stdout.decode("utf-8")


def _add_sh(args) -> str:
    """
    Add the changes.

    Args:
        args (argparse.Namespace): The arguments.

    Returns:
        str: The output of the git add command.
    """
    return subprocess.run(
        ["git", "add", "-u"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    ).stdout.decode("utf-8")


def _git(args):
    commands = {
        "commit-message": _commit_message,
        "commit": _commit,
        "push": _push_sh,
        "pull": _pull_sh,
        "add": _add_sh,
    }

    return commands[args.input_args[1]](args)


class GitFile:
    """A git file with its diff contents."""

    def __init__(self, file_name, diff):
        """Initialize a GitFile object.
        Args:
            file_name (str): The name of the file.
            diff (str): The diff contents of the file.
        """
        self.file_name = file_name
        self.diff = diff
