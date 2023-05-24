"""Summarize the changes in a release."""
from curses.ascii import isdigit
import csv
import os
from gpt_review._review import _summarize_files
from gpt_review.repositories.devops import DevOpsClient
import summarizations.constants as C

access_token = os.getenv("MSDATA_ADO_TOKEN")

# The repository and pull_request parameters are not being used in the function
# This might be problematic for the for loop
# pr_id is not being used in the function, why is that?
# diff = DevOpsClient.get_pr_diff(repository, pull_request, access_token)
# diff = DevOpsClient.get_pr_diff_link_parameter(pull_request_link, access_token)
# diff_summarization = _summarize_files(diff)
# print(diff_summarization)

pull_request_ids = []
with open("/workspaces/gpt-review/src/summarizations/pull_request_list.csv", "r") as f:
    csv_file = csv.reader(f)
    for line in csv_file:
        if line[0].isdigit():
            pull_request_ids.append(line[0])

# do 10 summaries at a time
lower_number = 0
upper_number = 10
pull_request_ids_length = len(pull_request_ids)
remainder = len(pull_request_ids) % upper_number
summary_group = []
summaries = []

while lower_number < upper_number:
    for pr_id in pull_request_ids[lower_number:upper_number]:
        pull_request_link = C.PRROOT + pr_id
        diff = DevOpsClient.get_pr_diff_link_parameter(pull_request_link, access_token)
        diff_summarization = _summarize_files(diff)
        summary_group.append(diff_summarization)
    lower_number += 9 if lower_number == 0 else 10
    upper_number += 10
    summaries.append(_summarize_files(summary_group))
