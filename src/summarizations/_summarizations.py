"""Summarize the changes in a release."""
from curses.ascii import isdigit
import csv
import os
import time
from gpt_review.repositories.devops import DevOpsClient
import summarizations.constants as C

start = time.process_time()

# access_token = os.getenv("MSDATA_ADO_TOKEN")
access_token = os.getenv("ADO_TOKEN")

# The repository and pull_request parameters are not being used in the function
# This might be problematic for the for loop
# pr_id is not being used in the function, why is that?
# diff = DevOpsClient.get_pr_diff(repository, pull_request, access_token)
# diff = DevOpsClient.get_pr_diff_link_parameter(pull_request_link, access_token)
# diff_summarization = DevOpsClient.post_pr_summary(diff)
# print(diff_summarization)

# todo make this a function load_pull_request_ids()
pull_request_ids = []
with open("/workspaces/gpt-review/src/summarizations/msazure_pull_request_list.csv", "r") as f:
    csv_file = csv.reader(f)
    for line in csv_file:
        if line[0].isdigit():
            pull_request_ids.append(line[0])

# todo make this into a function summarize_pull_requests()
summaries = []
diffs = []
# todo do all summaries first and then summarize the summaries 10 at a time
# TODO PRIORITIZE THIS, WHY ARE THE DIFFS EQUAL?? diffs[0]  == diffs[1] == diffs[2] -> True
# it's catching the diff? and providing summaries on the same diff? investigate further
for pr_id in pull_request_ids:
    pull_request_link = C.MSAZURE_PATCHREPO + pr_id
    diff = DevOpsClient.get_pr_diff(C.MSAZURE_PATCHREPO, C.MSAZURE_PRID, access_token)
    diffs.append(diff)
    summary = DevOpsClient.post_pr_summary(
        diff=diff, link=C.MSAZURE_PATCHREPO + C.MSAZURE_PRID, access_token=access_token
    )
    print(time.process_time() - start)
    summaries.append(summary)


print(summaries)

# MSAZURE
# diff = DevOpsClient.get_pr_diff(C.MSAZURE_PATCHREPO, C.MSAZURE_PRID, access_token)
# summary = DevOpsClient.post_pr_summary(diff=diff, link=C.MSAZURE_PATCHREPO + C.MSAZURE_PRID, access_token=access_token)
# print(summary)

# MSDATA
# diff = DevOpsClient.get_pr_diff(C.MSDATA_PATCHREPO, C.MSDATA_PRID, access_token)
# summary = DevOpsClient.post_pr_summary(diff=diff, link=C.MSDATA_PATCHREPO + C.MSDATA_PRID, access_token=access_token)
# print(summary)
