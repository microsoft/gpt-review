# Summary by GPT-4
The changes in this PR add new input options to the `action.yml` file and update the `review.py` script to handle these new options. The new input options are related to risk assessment and summary generation for different aspects of a PR, such as configuration changes, schema changes, features, feature flags, and incidents.

The `review.py` script is updated with a new `CHECKS` dictionary that contains two lists: `SUMMARY_CHECKS` and `RISK_CHECKS`. Each list contains dictionaries with information about different checks that can be performed on a PR.

The `summarize_pr()` function is updated to use the new checks from the `CHECKS` dictionary. It now calls the `check_goals()` function with the appropriate list of checks based on whether it's generating a full summary or a risk summary.

A new function called `summarize_risk()` is added to generate a risk summary for a PR using the risk-related checks from the `CHECKS` dictionary.

The existing functions like `summarize_files()`, `summarize_bugs_in_pr()`, and others are also updated to work with these changes.

## Overview
The main goal of this PR is to add new input options to the `action.yml` file and update the `review.py` script to handle these new options. The new input options are related to risk assessment and summary generation for different aspects of a PR, such as configuration changes, schema changes, features, feature flags, and incidents.

### Suggestions

Here are some suggestions for improving the changes in this PR:

1. Update the descriptions of the new input variables in `action.yml` to accurately describe their purpose, as they all currently have the same description: "Include summary of potential breaking changes".

2. In the `request_goals` function, consider initializing `messages` as an empty list before the loop and then appending each prompt to it within the loop. This way, you can avoid creating a new list for each iteration.

3. In the `summarize_pr` function, consider renaming the variable `text` to something more descriptive like `pr_summary`.

4. In the `summarize_risk` function, consider renaming the variable `text` to something more descriptive like `risk_summary`.

5. Add comments and docstrings to new functions like `request_goals`, `request_goal`, and `check_goals` to provide more context on their purpose and usage.

6. Consider adding type hints for function arguments and return values for better readability and maintainability.

7. In the `call_gpt4` function, add a default value for the new parameter `messages`. This will ensure that existing calls to this function without specifying this parameter will still work correctly.

Overall, these changes should help improve code readability and maintainability while also providing more accurate descriptions for new input variables in action.yml.

### Configuration Changes

The configuration changes added new input options to the action.yml file. These options include RISK_SUMMARY, RISK_ROLLBACK, RISK_BREAKING, RISK_FLAGGED, SUMMARY_CONFIG, SUMMARY_SCHEMA, SUMMARY_FEATURES, SUMMARY_FLAGS, and SUMMARY_INCIDENTS. Each of these options has a description, default value (true), required status (false), and type (string).

Additionally, the review.py file has been updated with new functions and changes to existing functions. A new CHECKS dictionary has been added containing two lists: SUMMARY_CHECKS and RISK_CHECKS. The call_gpt4 function now accepts an optional messages parameter. The call_gpt function has also been updated to accept an optional prompt parameter and messages parameter.

New functions have been added: request_goals, request_goal, summarize_pr, summarize_risk, and check_goals. The existing functions summarize_bugs_in_pr and summarize_files have been updated as well.

These changes aim to improve the functionality of the code by providing more options for summarizing PRs and assessing potential risks in the code changes.

### Schema Changes

The schema changes in this diff include the addition of several new input fields in the action.yml file. These fields are related to risk summary, rollback capability, breaking changes, flagged risks, configuration changes, schema changes, features, feature flags, and incidents. The default value for each of these fields is set to true.

In the review.py file, a new dictionary called CHECKS has been added which contains two lists: SUMMARY_CHECKS and RISK_CHECKS. Each list contains dictionaries with flag, header, and goal keys. Several new functions have been added as well: request_goals(), request_goal(), summarize_pr(), summarize_risk(), and check_goals(). These functions are used to generate summaries and risk assessments based on the git diff provided.

Overall, these changes seem to enhance the functionality of the code by providing more detailed summaries and risk assessments for pull requests.

### Features

The following features were added:

1. RISK_SUMMARY: Include summary of potential breaking changes.
2. RISK_ROLLBACK: Include summary of potential breaking changes.
3. RISK_BREAKING: Include summary of potential breaking changes.
4. RISK_FLAGGED: Include summary of potential breaking changes.
5. SUMMARY_CONFIG: Include summary of potential breaking changes.
6. SUMMARY_SCHEMA: Include summary of potential breaking changes.
7. SUMMARY_FEATURES: Include summary of potential breaking changes.
8. SUMMARY_FLAGS: Include summary of potential breaking changes.
9. SUMMARY_INCIDENTS: Include summary of potential breaking changes.

These features are added as input options in the action.yml file and are used in the review.py script to generate summaries and risk assessments for different aspects of a pull request, such as configuration changes, schema updates, new features, feature flags, and incidents related to the code change.

### Feature Flags

Yes, there are feature flags added in this commit. The following feature flags have been added:

- RISK_SUMMARY
- RISK_ROLLBACK
- RISK_BREAKING
- RISK_FLAGGED
- SUMMARY_CONFIG
- SUMMARY_SCHEMA
- SUMMARY_FEATURES
- SUMMARY_FLAGS
- SUMMARY_INCIDENTS

### Incidents

The changes in this PR appear to be focused on enhancing the code review process by adding more options for summarizing potential risks and incidents. The new options include summaries for configuration changes, schema changes, features, feature flags, and incidents. These additional summaries aim to provide a more comprehensive understanding of the changes made in a pull request and any potential risks associated with them.

## Risks


### Rollback Capability

The changes in this PR include additional risk-related checks and summaries for potential breaking changes, rollback capability, flagged risks, configuration changes, schema changes, features, feature flags, and incidents. These checks can help identify potential issues and risks associated with the changes in a PR.

However, it is important to note that while these checks can provide valuable insights into the potential risks associated with a PR, they may not cover all possible scenarios or issues. It is still essential to have a thorough manual review process in place to ensure that all potential risks are identified and addressed.

Regarding rollback capability concerns (typically associated with schema-related changes), this PR does not seem to introduce any direct schema-related changes. However, it is always recommended to have a rollback plan in place for any significant changes made to your application or database schema. This may include having database backups available or implementing feature flags to quickly disable new features if issues arise.

In summary, this PR adds valuable risk-related checks and summaries that can help identify potential issues and risks associated with the changes in a PR. However, it is still essential to have a thorough manual review process in place to ensure that all potential risks are identified and addressed.

### Breaking Changes

There are no breaking changes detected in this git diff. All the new parameters added to public functions have default values and are not required.

### Flagged Risks

There is no explicit risk flagged in the code or comments. However, it's important to note that this code adds new input options for the GitHub action and modifies some functions to include additional checks and summaries related to potential risks and breaking changes. It is recommended to thoroughly test these changes before integrating them into a production environment.
