"""Pytest for gpt_review/main.py"""
from dataclasses import dataclass
import os
import pytest
import subprocess
import sys

from gpt_review._gpt_cli import cli
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
        "ask how are you --max-tokens 0", CLIError, "b'ERROR: --max_tokens must be an integer between 1 and 4000\\n'"
    ),
    TestCase("ask how are you --temperature 1"),
    TestCase("ask how are you -t 0.5"),
    TestCase("ask how are you -t 9", CLIError, "b'ERROR: --temperature must be a float between 0 and 1\\n'"),
    TestCase("ask how are you --top-p 0.7"),
    TestCase("ask how are you --top-p 4.5", CLIError, "b'ERROR: --top-p must be a float between 0 and 1\\n'"),
    TestCase("ask how are you --frequency-penalty 1"),
    TestCase(
        "ask how are you --frequency-penalty 3",
        CLIError,
        "b'ERROR: --frequency-penalty must be a float between 0 and 2\\n'",
    ),
    TestCase("ask how are you --presence-penalty 0.7"),
    TestCase(
        "ask how are you --presence-penalty 8.7",
        CLIError,
        "b'ERROR: --presence-penalty must be a float between 0 and 2\\n'",
    ),
    TestCase("ask how are you --max-tokens=5 --temperature 0.1"),
    TestCase(
        "ask how are you --max-tokens 5 -t 8", CLIError, "b'ERROR: --temperature must be a float between 0 and 1\\n'"
    ),
    TestCase("ask how are you --max-tokens=5 --top-p 0.7"),
    TestCase(
        "ask how are you --max-tokens 5000 --top-p 0.7",
        CLIError,
        "b'ERROR: --max_tokens must be an integer between 1 and 4000\\n'",
    ),
    TestCase("ask how are you --frequency-penalty 1 --presence-penalty 0.7"),
    TestCase(
        "ask how are you --frequency-penalty 4 --presence-penalty 4",
        CLIError,
        "b'ERROR: --frequency-penalty must be a float between 0 and 2\\n'",
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

    if command.expected_error is not None:
        assert result.stderr.__str__() == command.expected_error_message
    else:
        assert result.returncode == 0


def gpt_cli_test(command):
    os.environ["GPT_ASK_COMMANDS"] = "1"

    sys.argv[1:] = command.command.split(" ")
    if "--help" in command.command:
        with pytest.raises(SystemExit):
            cli()
    elif command.expected_error is not None:
        exit_code = cli()
        assert exit_code == 1
    else:
        exit_code = cli()
        assert exit_code == 0


@pytest.mark.parametrize("command", ARGS)
@pytest.mark.integration
def test_int_gpt_cli(command):
    """Test gpt commands from installed CLI"""
    gpt_cli_test(command)


@pytest.mark.parametrize(
    "command",
    ARGS,
)
def test_gpt_cli(command, mock_openai):
    gpt_cli_test(command)
