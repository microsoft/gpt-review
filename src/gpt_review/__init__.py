#   -------------------------------------------------------------
#   Copyright (c) Microsoft Corporation. All rights reserved.
#   Licensed under the MIT License. See LICENSE in project root for information.
#   -------------------------------------------------------------
"""Easy GPT CLI"""
from __future__ import annotations

from knack.help_files import helps

__version__ = "0.7.2"


def _help_text(help_type, short_summary) -> str:
    return f"""
type: {help_type}
short-summary: {short_summary}
"""


helps[""] = _help_text("group", "Easily interact with GPT APIs.")
helps["git"] = _help_text("group", "Use GPT enchanced git commands.")
helps["github"] = _help_text("group", "Use GPT with GitHub Repositories.")
helps["devops"] = _help_text("group", "Use GPT with Azure DevOps Repositories.")
helps["review"] = _help_text("group", "Use GPT to review contents of a file.")
