"""The GPT CLI entry point for python -m gpt"""
from __future__ import annotations

import sys

from gpt_review._gpt_cli import cli

if __name__ == "__main__":
    exit_code = cli()
    sys.exit(exit_code)
