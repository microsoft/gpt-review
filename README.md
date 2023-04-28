# gpt-review

A Python based CLI and GitHub Action to use Open AI or Azure Open AI models to review contents of pull requests.

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
