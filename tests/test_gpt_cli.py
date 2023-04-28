"""Pytest for gpt_review/main.py"""
from dataclasses import dataclass
import os
import pytest
import subprocess
import sys

from gpt_review._gpt_cli import cli
from gpt_review.constants import (
    MAX_TOKENS_MIN,
    MAX_TOKENS_MAX,
    TEMPERATURE_MIN,
    TEMPERATURE_MAX,
    TOP_P_MIN,
    TOP_P_MAX,
    FREQUENCY_PENALTY_MIN,
    FREQUENCY_PENALTY_MAX,
    PRESENCE_PENALTY_MIN,
    PRESENCE_PENALTY_MAX,
)


@dataclass
class CLICase:
    command: str
    expected_error_message: str = ""
    expected_error_code: int = 0


ROOT_COMMANDS = [
    CLICase("--version"),
    CLICase("--help"),
]

ASK_COMMANDS = [
    CLICase("ask --help"),
    CLICase("ask how are you"),
    CLICase("ask how are you --max-tokens=5"),
    CLICase(
        "ask how are you --max-tokens",
        """usage: gpt ask [-h] [--verbose] [--debug] [--only-show-errors]
               [--output {json,jsonc,yaml,yamlc,table,tsv,none}]
               [--query JMESPATH] [--max-tokens MAX_TOKENS]
               [--temperature TEMPERATURE] [--top-p TOP_P]
               [--frequency-penalty FREQUENCY_PENALTY]
               [--presence-penalty PRESENCE_PENALTY]
               <QUESTION> [<QUESTION> ...]
gpt ask: error: argument --max-tokens: expected one argument
""",
        2,
    ),
    CLICase(
        "ask how are you --max-tokens 'test'",
        """usage: gpt ask [-h] [--verbose] [--debug] [--only-show-errors]
               [--output {json,jsonc,yaml,yamlc,table,tsv,none}]
               [--query JMESPATH] [--max-tokens MAX_TOKENS]
               [--temperature TEMPERATURE] [--top-p TOP_P]
               [--frequency-penalty FREQUENCY_PENALTY]
               [--presence-penalty PRESENCE_PENALTY]
               <QUESTION> [<QUESTION> ...]
gpt ask: error: argument --max-tokens: invalid int value: \"'test'\"
""",
        2,
    ),
    CLICase(
        f"ask how are you --max-tokens {MAX_TOKENS_MIN-1}",
        f"ERROR: --max-tokens must be a(n) int between {MAX_TOKENS_MIN} and {MAX_TOKENS_MAX}\n",
        1,
    ),
    CLICase("ask how are you --temperature 1"),
    CLICase(
        f"ask how are you --temperature {TEMPERATURE_MAX+8}",
        f"ERROR: --temperature must be a(n) float between {TEMPERATURE_MIN} and {TEMPERATURE_MAX}\n",
        1,
    ),
    CLICase("ask how are you --top-p 0.7"),
    CLICase(
        f"ask how are you --top-p {TOP_P_MAX+3.5}",
        f"ERROR: --top-p must be a(n) float between {TOP_P_MIN} and {TOP_P_MAX}\n",
        1,
    ),
    CLICase("ask how are you --frequency-penalty 1"),
    CLICase(
        f"ask how are you --frequency-penalty {FREQUENCY_PENALTY_MAX+2}",
        f"ERROR: --frequency-penalty must be a(n) float between {FREQUENCY_PENALTY_MIN} and {FREQUENCY_PENALTY_MAX}\n",
        1,
    ),
    CLICase("ask how are you --presence-penalty 0.7"),
    CLICase(
        f"ask how are you --presence-penalty {PRESENCE_PENALTY_MAX+7.7}",
        f"ERROR: --presence-penalty must be a(n) float between {PRESENCE_PENALTY_MIN} and {PRESENCE_PENALTY_MAX}\n",
        1,
    ),
    CLICase("ask how are you --max-tokens=5 --temperature 0.1"),
    CLICase("ask how are you --max-tokens=5 --top-p 0.7"),
    CLICase(
        f"ask how are you --max-tokens {MAX_TOKENS_MAX+1} --top-p 0.7",
        f"ERROR: --max-tokens must be a(n) int between {MAX_TOKENS_MIN} and {MAX_TOKENS_MAX}\n",
        1,
    ),
    CLICase("ask how are you --frequency-penalty 1 --presence-penalty 0.7"),
    CLICase(
        f"ask how are you --frequency-penalty {FREQUENCY_PENALTY_MAX+3} --presence-penalty {PRESENCE_PENALTY_MAX+7.7}",
        f"ERROR: --frequency-penalty must be a(n) float between {FREQUENCY_PENALTY_MIN} and {FREQUENCY_PENALTY_MAX}\n",
        1,
    ),
    CLICase("ask how are you --max-tokens=5 --temperature 0.1 --frequency-penalty 1 --presence-penalty 0.7"),
    CLICase("ask how are you --max-tokens=5 --top-p 0.7 --frequency-penalty 1 --presence-penalty 0.7"),
]

ARGS = ROOT_COMMANDS + ASK_COMMANDS


@pytest.mark.parametrize("command", ARGS)
@pytest.mark.cli
def test_cli_gpt_cli(command: CLICase) -> None:
    """Test gpt commands from installed CLI"""

    command_array = f"gpt {command.command}".split(" ")

    result = subprocess.run(
        command_array,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == command.expected_error_code


def gpt_cli_test(command: CLICase) -> None:
    os.environ["GPT_ASK_COMMANDS"] = "1"

    sys.argv[1:] = command.command.split(" ")

    try:
        exit_code = cli()
    except SystemExit as e:
        exit_code = e.code
    finally:
        assert exit_code == command.expected_error_code


@pytest.mark.parametrize("command", ARGS)
@pytest.mark.integration
def test_int_gpt_cli(command: CLICase) -> None:
    """Test gpt commands from CLI file"""
    gpt_cli_test(command)


@pytest.mark.parametrize(
    "command",
    ARGS,
)
def test_gpt_cli(command: CLICase, mock_openai: None) -> None:
    gpt_cli_test(command)
