"""Pytest for gpt_review/main.py"""
import os
import pytest
import subprocess
import sys

from gpt_review._gpt_cli import cli

ROOT_COMMANDS = [
    "--version",
    "--help",
]

ASK_COMMANDS = [
    "ask --help",
    "ask how are you",
    "ask how are you --max-tokens=5",
    # "ask how are you --max-tokens 0",
    "ask how are you --temperature 1",
    "ask how are you -t 0.5",
    # "ask how are you -t 9",
    "ask how are you --top-p 0.7",
    # "ask how are you --top-p 4.5",
    "ask how are you --frequency-penalty 1",
    # "ask how are you --frequency-penalty 3",
    "ask how are you --presence-penalty 0.7",
    # "ask how are you --presence-penalty 8.7",
    "ask how are you --max-tokens=5 --temperature 0.1",
    # "ask how are you --max-tokens 5 -t 8",
    "ask how are you --max-tokens=5 --top-p 0.7",
    # "ask how are you --max-tokens 5000 --top-p 0.7",
    "ask how are you --frequency-penalty 1 --presence-penalty 0.7",
    # "ask how are you --frequency-penalty 4 --presence-penalty 4",
    "ask how are you --max-tokens=5 --temperature 0.1 --frequency-penalty 1 --presence-penalty 0.7",
    "ask how are you --max-tokens=5 --top-p 0.7 --frequency-penalty 1 --presence-penalty 0.7",
]

ARGS = ROOT_COMMANDS + ASK_COMMANDS


@pytest.mark.parametrize("command", ARGS)
@pytest.mark.cli
def test_cli_gpt_cli(command):
    """Test gpt commands from installed CLI"""

    command_array = f"gpt {command}".split(" ")
    result = subprocess.run(
        command_array,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0


def gpt_cli_test(command):
    os.environ["GPT_ASK_COMMANDS"] = "1"

    sys.argv[1:] = command.split(" ")
    if "--help" in command:
        with pytest.raises(SystemExit):
            cli()
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
