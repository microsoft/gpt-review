"""Basic functions for requesting review based goals from GPT-4."""
import logging
import os

from gpt_review._ask import _ask

_CHECKS = {
    "SUMMARY_CHECKS": [
        {
            "flag": "SUMMARY_SUGGEST",
            "header": "Suggestions",
            "goal": "Any suggestions for improving the changes in this PR?",
        },
        {
            "flag": "SUMMARY_CONFIG",
            "header": "Configuration Changes",
            "goal": "Any configuration changes?",
        },
        {
            "flag": "SUMMARY_SCHEMA",
            "header": "Schema Changes",
            "goal": "Any schema changes?",
        },
        {
            "flag": "SUMMARY_FEATURES",
            "header": "Features",
            "goal": "What features where added?",
        },
        {
            "flag": "SUMMARY_FLAGS",
            "header": "Feature Flags",
            "goal": "Any feature flags added?",
        },
        {
            "flag": "SUMMARY_INCIDENTS",
            "header": "Incidents",
            "goal": "Any changes that appear to be in response to incidents?",
        },
    ],
    "RISK_CHECKS": [
        {
            "flag": "RISK_ROLLBACK",
            "header": "Rollback Capability",
            "goal": "Any concerns about rollback capability (ex: typically associated with schema-related changes)?",
        },
        {
            "flag": "RISK_BREAKING",
            "header": "Breaking Changes",
            "goal": """Detect breaking changes in a git diff. Here are some things that can cause a breaking change.
- new parameters to public functions which are required and have no default value.
""",
        },
        {
            "flag": "RISK_FLAGGED",
            "header": "Flagged Risks",
            "goal": "Anything flagged as a risk in the code/comments itself?",
        },
    ],
}


class GitFile:
    """A git file with its diff contents."""

    def __init__(self, file_name, diff) -> None:
        """Initialize a GitFile object.

        Args:
            file_name (str): The name of the file.
            diff (str): The diff contents of the file.
        """
        self.file_name = file_name
        self.diff = diff


def _request_goal(git_diff, goal) -> str:
    """
    Request a goal from GPT-4.

    Args:
        git_diff (str): The git diff to split.
        goal (str): The goal to request from GPT-4.

    Returns:
        response (str): The response from GPT-4.
    """
    prompt = f"""
{goal}

{git_diff}
"""

    response = _ask([prompt], max_tokens=1500)
    logging.info(response["response"])
    return response["response"]


def _check_goals(git_diff, checks, indent="###") -> str:
    """
    Check goals.

    Args:
        git_diff (str): The git diff to check.
        checks (list): The checks to run.

    Returns:
        str: The output of the checks.
    """
    return "".join(
        f"""
{indent} {check["header"]}

{_request_goal(git_diff, goal=check["goal"])}
"""
        for check in checks
        if os.getenv(check["flag"], "true").lower() == "true"
    )


def _summarize_pr(git_diff) -> str:
    """
    Summarize a PR.

    Args:
        git_diff (str): The git diff to summarize.

    Returns:
        str: The summary of the PR.
    """
    text = ""
    if os.getenv("FULL_SUMMARY", "true").lower() == "true":
        text += f"""
{_request_goal(git_diff, goal="")}
"""

        text += _check_goals(git_diff, _CHECKS["SUMMARY_CHECKS"])
    return text


def _summarize_file(diff) -> str:
    """Summarize a file in a git diff.

    Args:
        diff (str): The file to summarize.

    Returns:
        str: The summary of the file.
    """
    git_file = GitFile(diff.split(" b/")[0], diff)
    prompt = f"""
Summarize the changes to the file {git_file.file_name}.
- Do not include the file name in the summary.
- list the summary with bullet points
{diff}
"""
    response = _ask([prompt], temperature=0.0)
    return f"""
### {git_file.file_name}
{response}
"""


def _split_diff(git_diff):
    """Split a git diff into a list of files and their diff contents.

    Args:
        git_diff (str): The git diff to split.

    Returns:
        list: A list of tuples containing the file name and diff contents.
    """
    diff = "diff"
    git = "--git a/"
    return git_diff.split(f"{diff} {git}")[1:]  # Use formated string to prevent splitting


def _summarize_test_coverage(git_diff) -> str:
    """Summarize the test coverage of a git diff.

    Args:
        git_diff (str): The git diff to summarize.

    Returns:
        str: The summary of the test coverage.
    """
    files = {}
    for diff in _split_diff(git_diff):
        path = diff.split(" b/")[0]
        git_file = GitFile(path.split("/")[len(path.split("/")) - 1], diff)

        files[git_file.file_name] = git_file

    prompt = f"""
```
{git_diff}
```
Discuss if tests been included to cover the latest changes?
"""

    return _ask([prompt], temperature=0.0, max_tokens=1500)["response"]


def _summarize_bugs_in_pr(git_diff) -> str:
    """
    Summarize bugs that may be introduced.

    Args:
        git_diff (str): The git diff to split.

    Returns:
        response (str): The response from GPT-4.
    """
    gpt4_big_prompot = f"""
Summarize bugs that may be introduced.

{git_diff}
"""
    response = _ask([gpt4_big_prompot])
    logging.info(response["response"])
    return response["response"]


def _summarize_risk(git_diff) -> str:
    """
    Summarize potential risks.

    Args:
        git_diff (str): The git diff to split.

    Returns:
        response (str): The response from GPT-4.
    """
    text = ""
    if os.getenv("RISK_SUMMARY", "true").lower() == "true":
        text += """
## Potential Risks

"""
        text += _check_goals(git_diff, _CHECKS["RISK_CHECKS"])
    return text


def _summarize_files(git_diff) -> str:
    """Summarize git files."""
    summary = """
# Summary by GPT-4
"""

    summary += _summarize_pr(git_diff)

    if os.getenv("FILE_SUMMARY", "true").lower() == "true":
        file_summary = """
## Changes

"""
        file_summary += "".join(_summarize_file(diff) for diff in _split_diff(git_diff))
        if os.getenv("FILE_SUMMARY_FULL", "true").lower() == "true":
            summary += file_summary

        summary += f"""
### Summary of File Changes
{_request_goal(file_summary, goal="Summarize the changes to the files.")}
"""

    if os.getenv("TEST_SUMMARY", "true").lower() == "true":
        summary += f"""
## Test Coverage
{_summarize_test_coverage(git_diff)}
"""

    if os.getenv("BUG_SUMMARY", "true").lower() == "true":
        summary += f"""
## Potential Bugs
{_summarize_bugs_in_pr(git_diff)}
"""

    summary += _summarize_risk(git_diff)

    return summary
