"""Summarize the changes in a release."""
import csv
import time
import os
from pathlib import Path

from gpt_review.repositories.devops import DevOpsClient
from gpt_review._review import _ask
from gpt_review.prompts._prompt import LangChainPrompt
import summarizations.constants as C


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
        for line in csv_file:
            if line[0].isdigit():
                pull_request_ids_list.append(line[0])
    return pull_request_ids_list


def _summarize_pull_requests(pull_request_ids_list: list, patch_repo: str) -> list:
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
        pr_link = (
            patch_repo + pr_id
        )  # This is not a real link to a PR, but the link is needed to post the summary and this is not being done here
        diff = DevOpsClient.get_pr_diff(patch_repo, pr_id, access_token)
        summary = DevOpsClient.generate_pr_summary(diff=diff, link=pr_link, access_token=access_token)
        print(time.process_time() - start)
        summaries_list.append(summary)
    return summaries_list


def load_summary_yaml() -> LangChainPrompt:
    """Load the summary yaml."""
    yaml_path = os.getenv("PROMPT_SUMMARY", str(Path(__file__).parents[0].joinpath(C.SUMMARY_PROMPT_YAML)))
    return LangChainPrompt.load(yaml_path)


def _summarize_summary(summary_group) -> str:
    """Summarize a list of summaries.

    Args:
        summary (str): The summary to summarize.

    Returns:
        str: The summary of the summary.
    """

    question = load_summary_yaml().format(summaries=summary_group)
    response = _ask(question=[question], temperature=0.0)
    return response


def _summarize_summaries(summaries_list: list) -> list:
    """Summarize summaries.

    Args:
        summaries_list (list): The list of summaries.

    Returns:
        str: The summary of summaries.
    """

    summarized_summaries_list = []
    for i in range(0, len(summaries_list), 10):
        summary_group = summaries_list[i : i + 10]
        summarized_summaries_list.append(_summarize_summary(summary_group))
    return summarized_summaries_list


def _get_summary(summaries_list: list) -> str:
    """Get the final summary.

    Args:
        summarized_summaries_list (list): The list of the summaries of the PRs.

    Returns:
        str: The final summary.
    """
    summarized_summaries = _summarize_summaries(summaries_list)
    while len(summarized_summaries) > 1:
        summarized_summaries = _summarize_summaries(summarized_summaries)
    return summarized_summaries[0]["response"]


access_token = C.MSAZURE_ADO_TOKEN
pull_request_ids = _load_pull_request_ids(C.MSAZURE_PULL_REQUEST_LIST)
summaries = _summarize_pull_requests(pull_request_ids, C.MSAZURE_PATCHREPO)
final_summary = _get_summary(summaries)
print(final_summary)
