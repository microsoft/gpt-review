"""Pytest for gpt_review/main.py"""
from dataclasses import dataclass
import os
import pytest
import subprocess
import sys

from gpt_review._gpt_cli import cli
import gpt_review.constants as C


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
    CLICase("ask --fast how are you"),
    CLICase(f"ask how are you --fast --max-tokens={C.MAX_TOKENS_DEFAULT}"),
    CLICase(
        "ask how are you --fast --max-tokens",
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
        "ask how are you --fast --max-tokens 'test'",
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
        f"ask how are you --fast --max-tokens {C.MAX_TOKENS_MIN-1}",
        f"ERROR: --max-tokens must be a(n) int between {C.MAX_TOKENS_MIN} and {C.MAX_TOKENS_MAX}\n",
        1,
    ),
    CLICase(f"ask how are you --fast --temperature {C.TEMPERATURE_DEFAULT}"),
    CLICase(
        f"ask how are you --temperature {C.TEMPERATURE_MAX+8}",
        f"ERROR: --temperature must be a(n) float between {C.TEMPERATURE_MIN} and {C.TEMPERATURE_MAX}\n",
        1,
    ),
    CLICase(f"ask how are you --fast --top-p {C.TOP_P_DEFAULT}"),
    CLICase(
        f"ask how are you --top-p {C.TOP_P_MAX+3.5}",
        f"ERROR: --top-p must be a(n) float between {C.TOP_P_MIN} and {C.TOP_P_MAX}\n",
        1,
    ),
    CLICase(f"ask how are you --fast --frequency-penalty {C.FREQUENCY_PENALTY_DEFAULT}"),
    CLICase(
        f"ask how are you --frequency-penalty {C.FREQUENCY_PENALTY_MAX+2}",
        f"ERROR: --frequency-penalty must be a(n) float between {C.FREQUENCY_PENALTY_MIN} and {C.FREQUENCY_PENALTY_MAX}\n",
        1,
    ),
    CLICase(f"ask how are you --fast --presence-penalty {C.PRESENCE_PENALTY_DEFAULT}"),
    CLICase(
        f"ask how are you --presence-penalty {C.PRESENCE_PENALTY_MAX+7.7}",
        f"ERROR: --presence-penalty must be a(n) float between {C.PRESENCE_PENALTY_MIN} and {C.PRESENCE_PENALTY_MAX}\n",
        1,
    ),
    CLICase(f"ask how are you --fast --max-tokens={C.MAX_TOKENS_DEFAULT} --temperature {C.TEMPERATURE_DEFAULT}"),
    CLICase(f"ask how are you --fast --max-tokens={C.MAX_TOKENS_DEFAULT} --top-p {C.TOP_P_DEFAULT}"),
    CLICase(
        f"ask how are you --fast --max-tokens {C.MAX_TOKENS_MAX+1} --top-p {C.TOP_P_DEFAULT}",
        f"ERROR: --max-tokens must be a(n) int between {C.MAX_TOKENS_MIN} and {C.MAX_TOKENS_MAX}\n",
        1,
    ),
    CLICase(
        f"ask how are you --fast --frequency-penalty {C.FREQUENCY_PENALTY_DEFAULT} --presence-penalty {C.PRESENCE_PENALTY_DEFAULT}"
    ),
    CLICase(
        f"ask how are you --fast --frequency-penalty {C.FREQUENCY_PENALTY_MAX+3} --presence-penalty {C.PRESENCE_PENALTY_MAX+7.7}",
        f"ERROR: --frequency-penalty must be a(n) float between {C.FREQUENCY_PENALTY_MIN} and {C.FREQUENCY_PENALTY_MAX}\n",
        1,
    ),
    CLICase(
        f"ask how are you --fast --max-tokens={C.MAX_TOKENS_DEFAULT} --temperature {C.TEMPERATURE_DEFAULT} --frequency-penalty {C.FREQUENCY_PENALTY_DEFAULT} --presence-penalty {C.FREQUENCY_PENALTY_MAX}"
    ),
    CLICase(
        f"""ask how are you --fast --max-tokens {C.MAX_TOKENS_DEFAULT} --top-p {C.TOP_P_DEFAULT} --frequency-penalty {C.FREQUENCY_PENALTY_DEFAULT} --presence-penalty {C.FREQUENCY_PENALTY_MAX}"""
    ),
    CLICase(
        "ask --files src/gpt_review/main.py --files src/gpt_review/main.py what programming language is this code written in?"
    ),
    CLICase("git commit --help"),
    # CLICase("git commit"),
    CLICase("github review --help"),
    CLICase("github review"),
    CLICase(
        "ask --files src/gpt_review/__init__.py --files src/gpt_review/__init__.py what programming language is this code written in?"
    ),
    CLICase("ask --fast -f src/gpt_review/__init__.py what programming language is this code written in?"),
]

ARGS = ROOT_COMMANDS + ASK_COMMANDS


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
