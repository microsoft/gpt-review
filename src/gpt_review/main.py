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
helps["ask"] = _help_text("group", "Use GPT to ask questions.")
helps["git"] = _help_text("group", "Use GPT enchanced git commands.")
helps["git commit"] = _help_text("command", "Run git commit with a commit message generated by GPT.")
helps["github"] = _help_text("group", "Use GPT with GitHub Repositories.")
helps["github review"] = _help_text("command", "Review GitHub PR with Open AI, and post response as a comment.")
helps["review"] = _help_text("group", "Use GPT to perform customized reviews.")
helps["review diff"] = _help_text("command", "Review a git diff from file.")


exit_code = cli()
sys.exit(exit_code)
