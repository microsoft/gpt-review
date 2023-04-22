"""GPT CLI"""
import os
import sys
from collections import OrderedDict

from knack import CLI, CLICommandsLoader
from knack.help_files import helps

import easy_gpt
from easy_gpt._ask import AskCommandGroup
from easy_gpt._gpt_cli import GPTCLI, GPTCommandsLoader, cli
from easy_gpt._git import GitCommandGroup


def _help_text(help_type, short_summary) -> str:
    return f"""
type: {help_type}
short-summary: {short_summary}
"""


helps[""] = _help_text("group", "Easily interact with GPT APIs.")
helps["git"] = _help_text("group", "Use GPT enchanced git commands.")


exit_code = cli()
sys.exit(exit_code)
