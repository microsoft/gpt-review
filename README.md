# gpt-review

<p align="center">
<a href="https://github.com/microsoft/gpt-review/actions"><img alt="Actions Status" src="https://github.com/microsoft/gpt-review/workflows/Python%20CI/badge.svg"></a>
<a href="https://codecov.io/gh/microsoft/gpt-review"><img alt="Coverage Status" src="https://codecov.io/gh/microsoft/gpt-review/branch/main/graph/badge.svg"></a>
<a href="https://github.com/microsoft/gpt-review/blob/main/LICENSE"><img alt="License: MIT" src="https://black.readthedocs.io/en/stable/_static/license.svg"></a>
<a href="https://pypi.org/project/gpt-review/"><img alt="PyPI" src="https://img.shields.io/pypi/v/gpt-review"></a>
<a href="https://pepy.tech/project/gpt-review"><img alt="Downloads" src="https://pepy.tech/badge/gpt-review"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

A Python based CLI and GitHub Action to use Open AI or Azure Open AI models to review contents of pull requests.

## How to install CLI

First, install the package via `pip`:

```bash
pip install gpt-review
```

### GPT API credentials

You will need to provide an OpenAI API key to use this CLI tool. In order of precedence, it will check the following methods:

1. Presence of a context file at `azure.yaml` or wherever `CONTEXT_FILE` points to. See `azure.yaml.template` for an example.

2. `AZURE_OPENAI_API_URL` and `AZURE_OPENAI_API_KEY` to connect to an Azure OpenAI API:

    ```bash
    export AZURE_OPENAI_API=<your azure api url>
    export AZURE_OPENAI_API_KEY=<your azure key>
    ```

3. `OPENAI_API_KEY` for direct use of the OpenAI API

    ```bash
    export OPENAI_API_KEY=<your openai key>
    ```

4. `AZURE_KEY_VAULT_URL` to use Azure Key Vault. Put secrets for the url at `azure-open-ai` and the API Key `azure-openai-key`, then run:

    ```bash
    export AZURE_KEY_VAULT_URL=https://<keyvault_name>.vault.azure.net/
    az login
    ```

## Main Commands

To show help information about available commands and their usage, run:

```bash
gpt --help
```

To display the current version of this CLI tool, run:

```bash
gpt --version
```

Here are the main commands for using this CLI tool:

### 1. Ask a Question

To submit a question to GPT and receive an answer, use the following format:

```bash
gpt ask "What is the capital of France?"
```

You can customize your request using various options like maximum tokens (`--max-tokens`), temperature (`--temperature`), top-p value (`--top-p`), frequency penalty (`--frequency-penalty`), presence penalty (`--presence-penalty`), etc.

#### Ask a Question about a File

To submit a question to GPT with a file and receive an answer, use the following format:

```bash
gpt ask --files WordDocument.docx "Summarize the contents of this document."
```

### 2. Review a PR

To review a PR, use the following format:

```bash
gpt github review \
    --access-token $GITHUB_ACCESS_TOKEN \
    --pull-request $PULL_REQUEST_NUMBER \
    --repository $REPOSITORY_NAME
```

### 3. Generate a git commit message with GPT

To generate a git commit message with GPT after having added the files, use the following format:

```bash
git add .

gpt git commit
```

For more detailed information on each command and its options, run:

```bash
gpt COMMAND --help
```

Replace COMMAND with one of the main commands listed above (e.g., 'ask').

## Developer Setup

To install the package in development mode, with additional packages for testing, run the following command:

```bash
pip install -e .[test]
```
