"""Pytest for gpt_review/main.py"""
from dataclasses import dataclass
import os
import pytest
import subprocess
import sys

from gpt_review._gpt_cli import cli
from gpt_review.constants import (
    MIN_MAX_TOKENS_VALUE,
    MAX_MAX_TOKENS_VALUE,
    MIN_TEMPERATURE_VALUE,
    MAX_TEMPERATURE_VALUE,
    MIN_TOP_P_VALUE,
    MAX_TOP_P_VALUE,
    MIN_FREQUENCY_PENALTY_VALUE,
    MAX_FREQUENCY_PENALTY_VALUE,
    MIN_PRESENCE_PENALTY_VALUE,
    MAX_PRESENCE_PENALTY_VALUE,
)

from knack.util import CLIError


@dataclass
class TestCase:
    command: str
    expected_error: CLIError = None
    expected_error_message: str = ""


ROOT_COMMANDS = [
    TestCase("--version"),
    TestCase("--help"),
]

ASK_COMMANDS = [
    TestCase("ask --help"),
    TestCase("ask how are you"),
    TestCase("ask how are you --max-tokens=5"),
    TestCase(
        "ask how are you --max-tokens",
        CLIError,
        "usage: gpt ask [-h] [--verbose] [--debug] [--only-show-errors]\n               [--output {json,jsonc,yaml,yamlc,table,tsv,none}]\n               [--query JMESPATH] [--max-tokens MAX_TOKENS]\n               [--temperature TEMPERATURE] [--top-p TOP_P]\n               [--frequency-penalty FREQUENCY_PENALTY]\n               [--presence-penalty PRESENCE_PENALTY]\n               <QUESTION> [<QUESTION> ...]\ngpt ask: error: argument --max-tokens: expected one argument\n",
    ),
    TestCase(
        "ask how are you --max-tokens 'test'",
        CLIError,
        "usage: gpt ask [-h] [--verbose] [--debug] [--only-show-errors]\n               [--output {json,jsonc,yaml,yamlc,table,tsv,none}]\n               [--query JMESPATH] [--max-tokens MAX_TOKENS]\n               [--temperature TEMPERATURE] [--top-p TOP_P]\n               [--frequency-penalty FREQUENCY_PENALTY]\n               [--presence-penalty PRESENCE_PENALTY]\n               <QUESTION> [<QUESTION> ...]\ngpt ask: error: argument --max-tokens: invalid int value: \"'test'\"\n",
    ),
    TestCase(
        "ask how are you --max-tokens 0",
        CLIError,
        f"ERROR: --max-tokens must be a(n) int between {MIN_MAX_TOKENS_VALUE} and {MAX_MAX_TOKENS_VALUE}\n",
    ),
    TestCase("ask how are you --temperature 1"),
    TestCase("ask how are you -t 0.5"),
    TestCase(
        "ask how are you -t 9",
        CLIError,
        f"ERROR: --temperature must be a(n) float between {MIN_TEMPERATURE_VALUE} and {MAX_TEMPERATURE_VALUE}\n",
    ),
    TestCase("ask how are you --top-p 0.7"),
    TestCase(
        "ask how are you --top-p 4.5",
        CLIError,
        f"ERROR: --top-p must be a(n) float between {MIN_TOP_P_VALUE} and {MAX_TOP_P_VALUE}\n",
    ),
    TestCase("ask how are you --frequency-penalty 1"),
    TestCase(
        "ask how are you --frequency-penalty 3",
        CLIError,
        f"ERROR: --frequency-penalty must be a(n) float between {MIN_FREQUENCY_PENALTY_VALUE} and {MAX_FREQUENCY_PENALTY_VALUE}\n",
    ),
    TestCase("ask how are you --presence-penalty 0.7"),
    TestCase(
        "ask how are you --presence-penalty 8.7",
        CLIError,
        f"ERROR: --presence-penalty must be a(n) float between {MIN_PRESENCE_PENALTY_VALUE} and {MAX_PRESENCE_PENALTY_VALUE}\n",
    ),
    TestCase("ask how are you --max-tokens=5 --temperature 0.1"),
    TestCase(
        "ask how are you --max-tokens 5 -t 8",
        CLIError,
        f"ERROR: --temperature must be a(n) float between {MIN_TEMPERATURE_VALUE} and {MAX_TEMPERATURE_VALUE}\n",
    ),
    TestCase("ask how are you --max-tokens=5 --top-p 0.7"),
    TestCase(
        "ask how are you --max-tokens 5000 --top-p 0.7",
        CLIError,
        f"ERROR: --max-tokens must be a(n) int between {MIN_MAX_TOKENS_VALUE} and {MAX_MAX_TOKENS_VALUE}\n",
    ),
    TestCase("ask how are you --frequency-penalty 1 --presence-penalty 0.7"),
    TestCase(
        "ask how are you --frequency-penalty 4 --presence-penalty 4",
        CLIError,
        f"ERROR: --frequency-penalty must be a(n) float between {MIN_FREQUENCY_PENALTY_VALUE} and {MAX_FREQUENCY_PENALTY_VALUE}\n",
    ),
    TestCase("ask how are you --max-tokens=5 --temperature 0.1 --frequency-penalty 1 --presence-penalty 0.7"),
    TestCase("ask how are you --max-tokens=5 --top-p 0.7 --frequency-penalty 1 --presence-penalty 0.7"),
]

ARGS = ROOT_COMMANDS + ASK_COMMANDS


@pytest.mark.parametrize("command", ARGS)
@pytest.mark.cli
def test_cli_gpt_cli(command):
    """Test gpt commands from installed CLI"""

    command_array = f"gpt {command.command}".split(" ")

    result = subprocess.run(
        command_array,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if command.expected_error:
        assert result.stderr.decode("ascii") == command.expected_error_message
    else:
        assert result.returncode == 0


def gpt_cli_test(command):
    os.environ["GPT_ASK_COMMANDS"] = "1"

    sys.argv[1:] = command.command.split(" ")
    if "--help" in command.command:
        with pytest.raises(SystemExit):
            cli()
    elif command.expected_error:
        # TODO
        try:
            exit_code = cli()
            assert exit_code == 1
        except SystemExit as e:
            # assert e.message == command.expected_error_message[: command.expected_error_message.rfind("error")]
            assert e.code == 2
    else:
        exit_code = cli()
        assert exit_code == 0


@pytest.mark.parametrize("command", ARGS)
@pytest.mark.integration
def test_int_gpt_cli(command):
    """Test gpt commands from CLI file"""
    gpt_cli_test(command)


@pytest.mark.parametrize(
    "command",
    ARGS,
)
def test_gpt_cli(command, mock_openai):
    gpt_cli_test(command)
