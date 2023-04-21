"""Review GitHub PR using Open AI Models like Davinci-003, GPT-3 and GPT-4."""
import logging
import json
import os
import time
import sys
import requests
import openai

from openai.error import RateLimitError, InvalidRequestError


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


def chunks(string, length):
    """Split a string into chunks of a given length.

    Args:
        string (str): The string to split.
        length (int): The length of the chunks.

    Yields:
        str: A chunk of the string.
    """
    for start in range(0, len(string), length):
        yield string[start : start + length]


def splits(string):
    """Split a string into chunks of 3000 characters.

    Args:
        string (str): The string to split.

    Yields:
        str: A chunk of the string.
    """
    for commit in string.split("From: "):
        # for split in commit.split("diff"):
        yield chunks(commit, 3000)


def call_davinci(
    prompt: str,
    temperature=0.10,
    max_tokens=312,
    top_p=1,
    frequency_penalty=0.5,
    presence_penalty=0.0,
) -> str:
    """Call the Davinci-003 model.

    Args:
        prompt (str): The prompt to send to GPT-3.
        temperature (float, optional): The temperature of the model. Defaults to 0.10.
        max_tokens (int, optional): The maximum number of tokens to return. Defaults to 312.
        top_p (float, optional): The top_p of the model. Defaults to 1.
        frequency_penalty (float, optional): The frequency penalty of the model. Defaults to 0.5.
        presence_penalty (float, optional): The presence penalty of the model. Defaults to 0.0.

    Returns:
        str: The response from the model.
    """
    model = os.getenv("GPT_MODEL", "text-davinci-003")

    logging.info("\nPrompt sent to GPT-3: %s", prompt)
    response = openai.Completion.create(
        engine=model,
        prompt=prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
    )
    return response["choices"][0]["text"]


def call_gpt3(
    prompt: str,
    temperature=0.10,
    max_tokens=312,
    top_p=1,
    frequency_penalty=0.5,
    presence_penalty=0.0,
    retry=0,
) -> str:
    """Call the GPT-3 model.

    Args:
        prompt (str): The prompt to send to GPT-3.
        temperature (float, optional): The temperature of the model. Defaults to 0.10.
        max_tokens (int, optional): The maximum number of tokens to return. Defaults to 312.
        top_p (float, optional): The top_p of the model. Defaults to 1.
        frequency_penalty (float, optional): The frequency penalty of the model. Defaults to 0.5.
        presence_penalty (float, optional): The presence penalty of the model. Defaults to 0.0.
        retry (int, optional): The number of retries. Defaults to 0.

    Returns:
        str: The response from the model.
    """
    try:
        logging.info("\nPrompt sent to GPT-3: %s\n", prompt)
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
        )
        logging.info(completion.choices[0].message.content)
        return completion.choices[0].message.content
    except InvalidRequestError as error:
        if retry < 5:
            time.sleep(retry * 5)
            return call_gpt3(
                prompt[:4097], temperature, max_tokens, top_p, frequency_penalty, presence_penalty, retry + 1
            )
        raise InvalidRequestError("Retry limit exceeded", error.param, error.code) from error
    except RateLimitError:
        return call_davinci(prompt, temperature, max_tokens, top_p, frequency_penalty, presence_penalty)


def _batch_gpt3(prompt: str) -> str:
    """Call GPT-3 in batches to avoid rate limit errors.

    Args:
        prompt (str): The prompt to send to GPT-3.
        batch_size (int, optional): The number of prompts to send at once. Defaults to 1.

    Returns:
        str: The response from GPT-3.
    """
    responses = "".join(
        call_gpt3(
            f"""
{chunk}
"""
        )
        for chunk in chunks(prompt, 4096)
    )
    return call_gpt3(
        f"""
Merge these pieces of text.

${responses}
"""
    )


def call_gpt4(
    prompt: str,
    temperature=0.10,
    max_tokens=500,
    top_p=1,
    frequency_penalty=0.5,
    presence_penalty=0.0,
    retry=0,
) -> str:
    """
    Call GPT-4 with the given prompt.

    Args:
        prompt (str): The prompt to send to GPT-4.
        temperature (float, optional): The temperature to use. Defaults to 0.10.
        max_tokens (int, optional): The maximum number of tokens to generate. Defaults to 500.
        top_p (float, optional): The top_p to use. Defaults to 1.
        frequency_penalty (float, optional): The frequency penalty to use. Defaults to 0.5.
        presence_penalty (float, optional): The presence penalty to use. Defaults to 0.0.
        retry (int, optional): The number of times to retry the request. Defaults to 0.

    Returns:
        str: The response from GPT-4.
    """
    try:
        engine = "gpt-4-32k"

        if len(prompt) > 32767:
            logging.warning("Prompt too long, truncating")
            prompt = prompt[:32767]

        logging.info("Prompt sent to GPT-4: %s\n", prompt)
        completion = openai.ChatCompletion.create(
            engine=engine,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
        )
        return completion.choices[0].message.content
    except InvalidRequestError:
        return call_gpt4(prompt[:32767], temperature, max_tokens, top_p, frequency_penalty, presence_penalty, retry + 1)
    except RateLimitError as error:
        if retry < 5:
            time.sleep(retry * 5)
            return call_gpt4(prompt, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, retry + 1)
        raise RateLimitError("Retry limit exceeded") from error


def call_gpt(
    prompt: str,
    temperature=0.10,
    max_tokens=500,
    top_p=1,
    frequency_penalty=0.5,
    presence_penalty=0.0,
) -> str:
    """Call GPT-3 or GPT-4 depending on the model.

    Args:
        prompt (str): The prompt to send to GPT-3 or GPT-4.
        temperature (float, optional): The temperature to use. Defaults to 0.10.
        max_tokens (int, optional): The maximum number of tokens to generate. Defaults to 500.
        top_p (float, optional): The top_p to use. Defaults to 1.
        frequency_penalty (float, optional): The frequency penalty to use. Defaults to 0.5.
        presence_penalty (float, optional): The presence penalty to use. Defaults to 0.0.

    Returns:
        str: The response from GPT-3 or GPT-4.
    """
    if os.getenv("AZURE_OPENAI_API_KEY"):
        openai.api_type = "azure"
        openai.api_base = os.getenv("AZURE_OPENAI_API")
        openai.api_version = "2023-03-15-preview"
        openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")

        return call_gpt4(prompt, temperature, max_tokens, top_p, frequency_penalty, presence_penalty)

    openai.api_key = os.getenv("OPENAI_API_KEY")
    return call_gpt3(prompt, temperature, max_tokens, top_p, frequency_penalty, presence_penalty)


def split_diff(git_diff):
    """Split a git diff into a list of files and their diff contents.

    Args:
        git_diff (str): The git diff to split.

    Returns:
        list: A list of tuples containing the file name and diff contents.
    """
    diff = "diff"
    git = "--git a/"
    return git_diff.split(f"{diff} {git}")[1:]  # Use formated string to prevent splitting


def _analyze_test_coverage_bicep(files):
    main_file = files["main.bicep"].diff
    test_file = files["main.test.bicep"].diff if "main.test.bicep" in files else ""

    return f"""
    Are the changes in main.bicep tested in main.test.bicep?
    If not, provide ideas how to test the changes, and create more tests in main.test.bicep.
    main.bicep
    ```
    {main_file}
    ```
    main.test.bicep
    ```
    {test_file}
    ```
    """


def summarize_test_coverage(git_diff):
    """Summarize the test coverage of a git diff.

    Args:
        git_diff (str): The git diff to summarize.

    Returns:
        str: The summary of the test coverage.
    """
    files = {}
    for diff in split_diff(git_diff):
        path = diff.split(" b/")[0]
        git_file = GitFile(path.split("/")[len(path.split("/")) - 1], diff)

        files[git_file.file_name] = git_file

    if "main.bicep" in files:
        prompt = _analyze_test_coverage_bicep(files)
    else:
        prompt = f"""
Are the changes tested?
```
{git_diff}
```
"""

    return call_gpt(prompt, temperature=0.0, max_tokens=1500)


def summarize_file(diff):
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
    response = call_gpt(prompt, temperature=0.0)
    return f"""
### {git_file.file_name}
{response}
"""


def summarize_pr(git_diff):
    """Summarize a git diff.

    Args:
        git_diff (str): The git diff to summarize.

    Returns:
        str: The summary of the git diff.
    """
    gpt4_big_prompot = f"""
{git_diff}
"""
    response = call_gpt(gpt4_big_prompot)
    logging.info(response)
    return response


def summarize_bugs_in_pr(git_diff):
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
    response = call_gpt(gpt4_big_prompot)
    logging.info(response)
    return response


def summarize_files(git_diff):
    """Summarize git files."""
    summary = """
# Summary by GPT-4
"""

    if(os.getenv("FULL_SUMMARY", "true").lower() == "true"):
        summary += f"""
{summarize_pr(git_diff)}
"""

    if(os.getenv("FILE_SUMMARY", "true").lower() == "true"):
        summary += """
## Changes
"""
        for diff in split_diff(git_diff):
            summary += summarize_file(diff)

    if(os.getenv("TEST_SUMMARY", "true").lower() == "true"):
        summary += f"""
## Test Coverage
{summarize_test_coverage(git_diff)}
"""

    if(os.getenv("BUG_SUMMARY", "true").lower() == "true"):
        summary += f"""
## Potential Bugs
{summarize_bugs_in_pr(git_diff)}
"""

    return summary


def get_review(pr_patch):
    """Get a review of a PR.

    Args:
        pr_patch (str): The patch of the PR.

    Returns:
        str: The review of the PR.
    """

    review = summarize_files(pr_patch)
    print(review)

    if os.getenv("LINK"):
        _post_pr_comment(review)
    else:
        logging.warning("No PR to post too")


def _post_pr_comment(review):
    git_commit_hash = os.getenv("GIT_COMMIT_HASH")
    data = {"body": review, "commit_id": git_commit_hash, "event": "COMMENT"}
    data = json.dumps(data)

    pr_link = os.getenv("LINK")
    owner = pr_link.split("/")[-4]
    repo = pr_link.split("/")[-3]
    pr_number = pr_link.split("/")[-1]

    access_token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "authorization": f"Bearer {access_token}",
    }
    response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews", headers=headers, timeout=10
    )
    comments = response.json()

    for comment in comments:
        if (
            "user" in comment
            and comment["user"]["login"] == "github-actions[bot]"
            and "body" in comment
            and "Summary by GPT-4" in comment["body"]
        ):
            review_id = comment["id"]
            data = {"body": review}
            data = json.dumps(data)

            response = requests.put(
                f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews/{review_id}",
                headers=headers,
                data=data,
                timeout=10,
            )
            logging.info(response.json())
            break
    else:
        # https://api.github.com/repos/OWNER/REPO/pulls/PULL_NUMBER/reviews
        response = requests.post(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
            headers=headers,
            data=data,
            timeout=10,
        )
        logging.info(response.json())


def _get_pr_diff():
    """
    Replicate the logic from this command

    PATCH_OUTPUT=$(curl --silent --request GET \
        --url https://api.github.com/repos/$PATCH_REPO/pulls/$PATCH_PR \
        --header "Accept: application/vnd.github.diff" \
        --header "Authorization: Bearer $GITHUB_TOKEN")
    """
    patch_repo = os.getenv("PATCH_REPO")
    patch_pr = os.getenv("PATCH_PR")
    access_token = os.getenv("GITHUB_TOKEN")

    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "authorization": f"Bearer {access_token}",
    }

    response = requests.get(f"https://api.github.com/repos/{patch_repo}/pulls/{patch_pr}", headers=headers, timeout=10)
    return response.text


if __name__ == "__main__":
    get_review(_get_pr_diff() if len(sys.argv) == 1 else sys.argv[1])
