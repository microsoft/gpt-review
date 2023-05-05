"""The GPT CLI entry point."""
import sys

from gpt_review._gpt_cli import cli


exit_code = cli()
sys.exit(exit_code)
