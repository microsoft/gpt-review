"""The GPT CLI entry point."""
import sys

from knack.help_files import helps

from gpt_review._gpt_cli import cli


def _help_text(help_type, short_summary) -> str:
    return f"""
type: {help_type}
short-summary: {short_summary}
"""


helps[""] = _help_text("group", "Easily interact with GPT APIs.")
helps["git"] = _help_text("group", "Use GPT enchanced git commands.")
helps["github"] = _help_text("group", "Use GPT with GitHub Repositories.")


exit_code = cli()
sys.exit(exit_code)
