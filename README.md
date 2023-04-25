# GPTReview Workflow 🤖🔍

Get OpenAI GPT models to suggest changes on your pull request in the comments.

## How to integrate into your repo:

1. Copy the workflow from this repo's .github/workflows/test-action.yml into your project in the same location and modify it to suit your needs, if you'd like. Update the action pointer from "./" to "microsoft/easy-gpt@<version>"
2. Get an [OpenAI API Key here](https://beta.openai.com/account/api-keys)
3. Get an [OpenAI Org ID here](https://beta.openai.com/account/org-settings)
4. Create two secrets in your project's settings called OPENAI_API_KEY for your OpenAI API Key and OPENAI_ORG_KEY for your OpenAI Organization ID..

## How to use CLI:

Install the package via `pip` and set the environment variables for your OpenAI API Key and Organization ID.
To use Azure OpenAI, set the environment variable `AZURE_OPENAI_API_URL` and `AZURE_OPENAI_API_URL_KEY` to the URL and key for your Azure OpenAI API.


```bash
pip install easy-gpt

export OPENAI_API_KEY=<your key>

export AZURE_OPENAI_API=<your azure api url>
export AZURE_OPENAI_API_KEY=<your azure key>

```

## Developer Setup
To install the package in development mode, with additional packages for testing, run the following command:

```bash
pip install -e .[test]
```
