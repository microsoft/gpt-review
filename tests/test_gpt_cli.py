"""Pytest for easy_gpt/main.py"""
import os
import pytest
import subprocess
import sys

ARGS = [
    "--version",
    "--help",
    # " ask --help",
    # "ask how are you",
    # "git --help",
    # "git status",
]


@pytest.mark.parametrize("command", ARGS)
def test_gpt_cli(command):
    """Test gpt --version"""
    result = subprocess.run(
        ["gpt", command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0


# def test_gpt_help():
#     """Test gpt --help"""
#     result = subprocess.run(
#         ["gpt", "--help"],
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE,
#         check=False,
#     )
#     assert result.returncode == 0
#     assert "Easily interact with GPT APIs." in result.stdout.decode("utf-8")


# def gpt_cli_test(command):
#     os.environ["GPT_ASK_COMMANDS"] = "1"

#     sys.argv[1:] = command.split(" ")
#     exit_code = cli()
#     assert exit_code == 0


# @pytest.mark.parametrize("command", ARGS)
# def test_gpt_cli(command):
#     gpt_cli_test(command)


# @pytest.mark.parametrize("command", ARGS)
# @pytest.mark.integration
# def test_int_gpt_cli(command):
#     gpt_cli_test(command)
