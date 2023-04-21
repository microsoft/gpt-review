"""Main module of the CLI."""
import argparse
import logging
from simple_gpt.llama import detect_programming_language, detect_repo_language, repo_question

from simple_gpt.shell.git import _git, _commit, _pull_sh, _push_sh, _add_sh

from simple_gpt.report import request_goal

from simple_gpt import __version__


def _mega_commit(args) -> str:
    """
    Super Commit Command.
    - Add updated and deleted files using 'git add -u' (skip with --no-add)
    - Commit the changes using 'git commit -m <message>', where <message> is the output of the GPT-4 model
    - Pull the changes using 'git pull origin HEAD' (skip with --no-pull)
    - Push the changes using 'git push origin HEAD' (skip with --no-push)

    Args:
        args (argparse.Namespace): The arguments.

    Returns:
        str: The output of the git commands.
    """
    output = ""
    if "no-add" not in args.input_args:
        logging.info("git add")
        output += _add_sh(args) + "\n"

    output += _commit(args)

    if "no-pull" not in args.input_args:
        logging.info("git pull")
        output += "\n" + _pull_sh(args)

    if "no-push" not in args.input_args:
        logging.info("git push")
        output += "\n" + _push_sh(args)

    return output


def _ask(args) -> str:
    return request_goal(args.input_args[1], "Try to answer the following question: ", max_tokens=1000)


def _generate(args) -> str:
    """
    Generate a commit message.

    gpt generate \
        $SAMPLE_ISSUE \
        $SAMPLE_DIFF \
        $NEW_ISSUE \
        "Use the 'sample issue' and 'sample solution',
            to create a new bicep module
            with a 'main.bicep', 'main.test.bicep', and 'README.md'
            that solves the new issue."
    Args:
        args (argparse.Namespace): The arguments.

    Returns:
        str: The output of the GPT-4 model.
    """
    sample_request = args.input_args[1]
    sample_solution = args.input_args[2]
    user_request = args.input_args[3]
    instructions = args.input_args[4]
    return request_goal(
        f"""
# Sample Issue
```md
{sample_request}
```

# Sample Solution
```md
{sample_solution}
```

# New Issue
```md
{user_request}
```
""",
        instructions,
        max_tokens=2000,
    )


def _detect_language(args) -> str:
    if len(args.input_args) > 3:
        return detect_programming_language(args.input_args[2], args.input_args[3])
    return detect_programming_language(args.input_args[2])


def _detect_repo_language(args) -> str:
    owner = args.input_args[2]
    repo = args.input_args[3]
    branch = args.input_args[4] if len(args.input_args) > 4 else "main"
    github_token = args.input_args[5] if len(args.input_args) > 5 else None
    index_path = args.input_args[6] if len(args.input_args) > 6 else "index.json"

    return detect_repo_language(owner, repo, branch, github_token, index_path)


def _repo_question(args) -> str:
    question = args.input_args[1]
    owner = args.input_args[2]
    repo = args.input_args[3]
    branch = args.input_args[4] if len(args.input_args) > 5 else "main"
    github_token = args.input_args[5] if len(args.input_args) > 6 else None
    index_path = args.input_args[6] if len(args.input_args) > 7 else "index.json"

    return repo_question(question, owner, repo, branch, github_token)


def _detect(args) -> str:
    """
    Detect the programming language of a file.

    Args:
        args (argparse.Namespace): The arguments.

    Returns:
        str: The output of the GPT-4 model.
    """
    detections = {
        "dir": _detect_language,
        "repo": _detect_repo_language,
    }
    return detections[args.input_args[1]](args)


def main():
    """Main function of the CLI."""
    parser = argparse.ArgumentParser(description="A simple CLI that prints input arguments.")
    parser.add_argument(
        "--version",
        help="Get Current Version Number",
        default=False,
        action="store_true",
    )
    parser.add_argument("input_args", default=[], metavar="ARG", nargs="*", help="Input arguments to be printed")
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return

    modules = {
        "git": _git,
        "ask": _ask,
        "commit": _mega_commit,
        "generate": _generate,
        "language": _detect,
        "repo": _repo_question,
    }
    print(modules[args.input_args[0]](args))
