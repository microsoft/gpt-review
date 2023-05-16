"""The GPT CLI entry point for python -m gpt"""
import sys

from gpt_review._gpt_cli import cli

if __name__ == "__main__":
    exit_code = cli()
    sys.exit(exit_code)
