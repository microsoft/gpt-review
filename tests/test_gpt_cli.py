"""Pytest for gpt_review/main.py"""
import os
import subprocess
import sys
from dataclasses import dataclass

import pytest

import gpt_review.constants as C
from gpt_review._gpt_cli import cli


@dataclass
class CLICase:
    command: str
    expected_error_message: str = ""
    expected_error_code: int = 0


@dataclass
class CLICase1(CLICase):
    expected_error_code: int = 1


@dataclass
class CLICase2(CLICase):
    expected_error_code: int = 2


SAMPLE_FILE = "src/gpt_review/__init__.py"
QUESTION = "how are you"
WHAT_LANGUAGE = "'what programming language is this code written in?'"
HELP_TEXT = """usage: gpt ask [-h] [--verbose] [--debug] [--only-show-errors]
               [--output {json,jsonc,yaml,yamlc,table,tsv,none}]
               [--query JMESPATH] [--max-tokens MAX_TOKENS]
               [--temperature TEMPERATURE] [--top-p TOP_P]
               [--frequency-penalty FREQUENCY_PENALTY]
               [--presence-penalty PRESENCE_PENALTY]
               <QUESTION> [<QUESTION> ...]
"""

ROOT_COMMANDS = [
    CLICase("--version"),
    CLICase("--help"),
]

ASK_COMMANDS = [
    CLICase("ask --help"),
    CLICase(f"ask {QUESTION}"),
    CLICase(f"ask --fast {QUESTION}"),
    CLICase(
        f"ask {QUESTION} --fast --max-tokens {C.MAX_TOKENS_DEFAULT} --temperature {C.TEMPERATURE_DEFAULT} --top-p {C.TOP_P_DEFAULT} --frequency-penalty {C.FREQUENCY_PENALTY_DEFAULT} --presence-penalty {C.FREQUENCY_PENALTY_MAX}"
    ),
    CLICase1(
        f"ask {QUESTION} --fast --max-tokens {C.MAX_TOKENS_MIN-1}",
        f"ERROR: --max-tokens must be a(n) int between {C.MAX_TOKENS_MIN} and {C.MAX_TOKENS_MAX}\n",
    ),
    CLICase1(
        f"ask {QUESTION} --temperature {C.TEMPERATURE_MAX+8}",
        f"ERROR: --temperature must be a(n) float between {C.TEMPERATURE_MIN} and {C.TEMPERATURE_MAX}\n",
    ),
    CLICase1(
        f"ask {QUESTION} --top-p {C.TOP_P_MAX+3.5}",
        f"ERROR: --top-p must be a(n) float between {C.TOP_P_MIN} and {C.TOP_P_MAX}\n",
    ),
    CLICase1(
        f"ask {QUESTION} --frequency-penalty {C.FREQUENCY_PENALTY_MAX+2}",
        f"ERROR: --frequency-penalty must be a(n) float between {C.FREQUENCY_PENALTY_MIN} and {C.FREQUENCY_PENALTY_MAX}\n",
    ),
    CLICase1(
        f"ask {QUESTION} --presence-penalty {C.PRESENCE_PENALTY_MAX+7.7}",
        f"ERROR: --presence-penalty must be a(n) float between {C.PRESENCE_PENALTY_MIN} and {C.PRESENCE_PENALTY_MAX}\n",
    ),
    CLICase2(
        f"ask {QUESTION} --fast --max-tokens",
        f"""{HELP_TEXT}
gpt ask: error: argument --max-tokens: expected one argument
""",
    ),
    CLICase2(
        f"ask {QUESTION} --fast --max-tokens 'test'",
        f"""{HELP_TEXT}
gpt ask: error: argument --max-tokens: invalid int value: \"'test'\"
""",
    ),
    CLICase(f"ask --files {SAMPLE_FILE} --files {SAMPLE_FILE} {WHAT_LANGUAGE} --reset"),
    CLICase(f"ask --fast -f {SAMPLE_FILE} {WHAT_LANGUAGE}"),
    CLICase(f"ask --fast -d src/gpt_review --reset --recursive --hidden --required-exts .py {WHAT_LANGUAGE}"),
    CLICase(f"ask --fast -repo microsoft/gpt-review --branch main {WHAT_LANGUAGE}"),
]

GITHUB_COMMANDS = [
    CLICase("github review --help"),
    CLICase("github review"),
]

GIT_COMMANDS = [
    CLICase("git commit --help"),
    # CLICase("git commit"),
    # CLICase("git commit --large"),
    # CLICase("git commit --gpt4"),
    # CLICase("git commit --push"),
]

REVIEW_COMMANDS = [
    CLICase("review --help"),
    CLICase("review diff --help"),
    CLICase("review diff --diff tests/mock.diff --config tests/config.summary.test.yml"),
    CLICase("review diff --diff tests/mock.diff --config tests/config.summary.extra.yml"),
]

ARGS = ROOT_COMMANDS + ASK_COMMANDS + GIT_COMMANDS + GITHUB_COMMANDS + REVIEW_COMMANDS
ARGS_DICT = {arg.command: arg for arg in ARGS}

MODULE_COMMANDS = [
    CLICase("python -m gpt --version"),
    CLICase("python -m gpt_review --version"),
]
MODULE_DICT = {arg.command: arg for arg in MODULE_COMMANDS}


def gpt_cli_test(command: CLICase) -> None:
    os.environ["GPT_ASK_COMMANDS"] = "1"

    sys.argv[1:] = command.command.split(" ")
    exit_code = -1
    try:
        exit_code = cli()
    except SystemExit as e:
        exit_code = e.code
    finally:
        assert exit_code == command.expected_error_code


def cli_test(command, command_array) -> None:
    result = subprocess.run(
        command_array,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == command.expected_error_code


@pytest.mark.parametrize("command", ARGS_DICT.keys())
@pytest.mark.cli
def test_cli_gpt_cli(command: str) -> None:
    """Test gpt commands from installed CLI"""
    command_array = f"gpt {ARGS_DICT[command].command}".split(" ")

    cli_test(ARGS_DICT[command], command_array)


@pytest.mark.parametrize("command", MODULE_DICT.keys())
@pytest.mark.cli
def test_cli_gpt_module(command: str) -> None:
    """Test running cli as module"""
    command_array = MODULE_DICT[command].command.split(" ")

    cli_test(MODULE_DICT[command], command_array)


@pytest.mark.parametrize("command", ARGS_DICT.keys())
def test_gpt_cli(command: str, mock_openai: None) -> None:
    gpt_cli_test(ARGS_DICT[command])


@pytest.mark.parametrize("command", ARGS_DICT.keys())
@pytest.mark.integration
def test_int_gpt_cli(command: str) -> None:
    """Test gpt commands from CLI file"""
    gpt_cli_test(ARGS_DICT[command])
