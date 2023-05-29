"""Summarize the changes in a release."""
import csv
import os
import time

from gpt_review.repositories.devops import DevOpsClient
import summarizations.constants as C

start = time.process_time()

access_token = os.getenv("MSDATA_ADO_TOKEN")
# access_token = os.getenv("ADO_TOKEN")


def load_pull_request_ids(file_path: str) -> list:
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


def summarize_pull_requests(pull_request_ids_list: list, patch_repo: str) -> list:
    """Summarize pull requests.

    Args:
        pull_request_ids_list (list): The list of pull request ids.
        patch_repo (str): The pointer to ADO in the format, org/project/repo.

    Returns:
        list: The list of summaries.
    """
    summaries_list = []
    for pr_id in pull_request_ids_list:
        pr_link = patch_repo + pr_id
        diff = DevOpsClient.get_pr_diff(patch_repo, pr_id, access_token)
        summary = DevOpsClient.post_pr_summary(diff=diff, link=pr_link, access_token=access_token)
        print(time.process_time() - start)
        summaries_list.append(summary)
    return summaries_list


# TODO make a function summarize_summaries()
# TODO do all summaries first and then summarize the summaries 10 at a time
# codebycopilot
def summarize_summaries(summaries_list: list) -> str:
    """Summarize summaries.

    Args:
        summaries_list (list): The list of summaries.

    Returns:
        str: The summary of summaries.
    """
    summary_of_summaries = ""
    for summary in summaries_list:
        summary_of_summaries += summary
    return summary_of_summaries


pull_request_ids = load_pull_request_ids(C.MSDATA_PULL_REQUEST_LIST)
summaries = summarize_pull_requests(pull_request_ids, C.MSDATA_PATCHREPO)
# final_summary = summarize_summaries(summaries)
