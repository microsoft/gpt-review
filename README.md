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

## How to use CLI:

Install the package via `pip` and set the environment variables for your OpenAI API Key and Organization ID.
To use Azure OpenAI, set the environment variable `AZURE_OPENAI_API_URL` and `AZURE_OPENAI_API_URL_KEY` to the URL and key for your Azure OpenAI API.


```bash
pip install gpt-review

export OPENAI_API_KEY=<your key>

export AZURE_OPENAI_API=<your azure api url>
export AZURE_OPENAI_API_KEY=<your azure key>

```

## Developer Setup
To install the package in development mode, with additional packages for testing, run the following command:

```bash
pip install -e .[test]
```
