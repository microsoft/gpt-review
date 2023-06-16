"""Summarize the changes in a release."""
import csv
import time
import os
from dataclasses import dataclass

import yaml

from gpt_review.repositories.devops import DevOpsClient
from gpt_review.prompts._prompt_pr_summary import load_batch_pr_summary_yaml, load_nature_yaml
from gpt_review.prompts._prompt import load_summary_yaml
from gpt_review._review import _ask
import gpt_review.constants as C

FILE_SUMMARY_NAME = (
    "/workspaces/gpt-review/scripts/summarizations/summaries/file_summary-"
    + str(time.strftime("%b-%d-%Y %H:%M:%S"))
    + ".txt"
)


@dataclass
class GitFile:
    """A git file with its diff contents."""

    file_name: str
    diff: str


def _print_to_file(file_path: str, text: str) -> None:
    """Print text to a file.

    Args:
        file_path (str): The path to the file.
        text (str): The text to print.
    """
    with open(file_path, "a+", encoding="utf-8") as file:
        file.write(text)


def _load_pull_request_ids(file_path: str) -> list:
    """Load pull request ids from a csv file.

    Args:
        file_path (str): The path to the csv file.

    Returns:
        list: The list of pull request ids.
    """
    pull_request_ids_list = []
    with open(file_path, "r", encoding="utf-8") as file:
        csv_file = csv.reader(file)
        pull_request_ids_list.extend(line[0] for line in csv_file if line[0].isdigit())
    return pull_request_ids_list


def _summarize_file(diff) -> str:
    """Summarize a file in a git diff.

    Args:
        diff (str): The file to summarize.

    Returns:
        str: The summary of the file.
    """
    question = load_summary_yaml().format(diff=diff)

    response = _ask(question=[question], temperature=0.0)
    return response["response"]


def _request_goal(git_diff, goal, fast: bool = False, large: bool = False, temperature: float = 0) -> str:
    """
    Request a goal from GPT-4.

    Args:
        git_diff (str): The git diff to split.
        goal (str): The goal to request from GPT-4.
        fast (bool, optional): Whether to use the fast model. Defaults to False.
        large (bool, optional): Whether to use the large model. Defaults to False.
        temperature (float, optional): The temperature to use. Defaults to 0.

    Returns:
        response (str): The response from GPT-4.
    """
    prompt = f"""
{goal}

{git_diff}
"""

    return _ask([prompt], max_tokens=1500, fast=fast, large=large, temperature=temperature)["response"]


def _summarize_pr_diff(diff) -> str:
    """Summarize a pull request diff.

    Args:
        diff (str): The diff to summarize.

    Returns:
        str: The summary.
    """
    summary = ""
    file_summary = "" + "".join(_summarize_file(file_diff) for file_diff in diff)
    summary += _request_goal(file_summary, goal="Summarize the changes to the files.")

    return summary


def get_pr_diff(patch_repo=None, patch_pr=None, pat=None) -> list:
    """
    Get the diff of a PR.

    Args:
        patch_repo (str): The pointer to ADO in the format, org/project/repo
        patch_pr (str): The PR id.
        pat (str): The ADO access token.
    """

    org = patch_repo.split("/")[0]
    project = patch_repo.split("/")[1]
    repo = patch_repo.split("/")[2]
    if patch_pr and pat:
        client = DevOpsClient(pat=pat, org=org, project=project, repository_id=repo)
        pull_request = client.client.get_pull_request_by_id(pull_request_id=patch_pr)
        return client.get_patches(pull_request_event=pull_request)
    return []


def _summarize_pull_requests(pull_request_ids_list: list, patch_repo: str, pat: str) -> list:
    """Summarize pull requests.

    Args:
        pull_request_ids_list (list): The list of pull request ids.
        patch_repo (str): The pointer to ADO in the format, org/project/repo.

    Returns:
        list: The list of summaries.
    """
    summaries_list = []
    for pr_id in pull_request_ids_list:
        start = time.process_time()
        if diff := get_pr_diff(patch_repo, pr_id, pat):
            summary = _summarize_pr_diff(diff=diff)
            print(time.process_time() - start)
            summaries_list.append(summary)
            summary_to_print = f"{pr_id}, {summary}\n"
            _print_to_file(FILE_SUMMARY_NAME, summary_to_print)
    return summaries_list


def _summarize_summary_batch(summary_batch: list) -> str:
    """Summarize a list of summaries.

    Args:
        summary (str): The summary to summarize.

    Returns:
        str: The summary of the summary.
    """

    question = load_batch_pr_summary_yaml().format(summaries=summary_batch)
    return _ask(question=[question], temperature=0.0)


def _summarize_summaries(summaries_list: list) -> list:
    """Summarize summaries.

    Args:
        summaries_list (list): The list of summaries.

    Returns:
        str: The summary of summaries.
    """

    summarized_summaries_list = []
    for i in range(0, len(summaries_list), 10):
        summary_batch = summaries_list[i : i + 10]
        summarized_summaries_list.append(_summarize_summary_batch(summary_batch))
    return summarized_summaries_list


def _get_final_summary(summaries_list: list) -> str:
    """Get the final summary.

    Args:
        summarized_summaries_list (list): The list of the summaries of the PRs.

    Returns:
        str: The final summary.
    """

    summarized_summaries = _summarize_summaries(summaries_list)
    while len(summarized_summaries) > 1:
        summarized_summaries = _summarize_summaries(summarized_summaries)
        summaries_to_print = f"{len(summarized_summaries)}, {summarized_summaries}\n"
        _print_to_file(FILE_SUMMARY_NAME, summaries_to_print)
    if summarized_summaries:
        return summarized_summaries[0]["response"]
    return "No summaries were provided."


def _get_deployment_nature(summary) -> str:
    """Get the nature of the deployment.

    Args:
        summary (str): The summary of the PRs in a deployment.

    Returns:
        str: The nature of the deployment.
    """
    question = load_nature_yaml().format(summary=summary)
    response = _ask(question=[question], temperature=0.0)
    return response["response"]


def _load_config_file():
    """Import from yaml file and return the config."""
    config_file = "scripts/summarizations/" + os.getenv("CONFIG_FILE", C.ADO_CONFIG_FILE)
    with open(config_file, "r", encoding="utf8") as file:
        return yaml.load(file, Loader=yaml.SafeLoader)


config = _load_config_file()
access_token = os.getenv(config.get("ado_token"))
pull_request_ids = _load_pull_request_ids(config.get("pull_request_list"))
summaries = _summarize_pull_requests(pull_request_ids, config.get("patch_repo"), access_token)
final_summary = _get_final_summary(summaries)
_print_to_file(FILE_SUMMARY_NAME, "\nThe final summary is:\n" + final_summary)

_print_to_file(FILE_SUMMARY_NAME, "\nThe nature of this deployment is: " + _get_deployment_nature(final_summary))
