"""GPT CLI"""
import os
import sys
from collections import OrderedDict

from knack import CLI, CLICommandsLoader
from knack.arguments import ArgumentsContext
from knack.commands import CommandGroup

from knack.help_files import helps

import easy_gpt


class GPTCommandsLoader(CLICommandsLoader):
    """The GPT CLI Commands Loader."""

    def load_command_table(self, args):
        with CommandGroup(self, "", "easy_gpt.ask#{}") as g:
            g.command("ask", "ask", is_preview=True)
        if os.getenv("GPT_GIT_COMMANDS"):
            with CommandGroup(self, "git", "easy_gpt._git#{}", is_experimental=True) as g:
                g.command("status", "_status")
        return OrderedDict(self.command_table)

    def load_arguments(self, command):
        with ArgumentsContext(self, "ask") as ac:
            ac.argument("question", type=str, help="Provide a question to ask GPT.")
        super(GPTCommandsLoader, self).load_arguments(command)


def _help_text(help_type, short_summary) -> str:
    return f"""
type: {help_type}
short-summary: {short_summary}
"""


helps[""] = _help_text("group", "Easily interact with GPT APIs.")
helps["git"] = _help_text("group", "Use GPT enchanced git commands.")


class GPTCLI(CLI):
    """Custom CLI implemntation to set version for the GPT CLI."""

    def get_cli_version(self):
        return easy_gpt.__version__


cli_name = "gpt"

gpt = GPTCLI(
    cli_name=cli_name,
    config_dir=os.path.expanduser(os.path.join("~", ".{}".format(cli_name))),
    config_env_var_prefix=cli_name,
    commands_loader_cls=GPTCommandsLoader,
)
exit_code = gpt.invoke(sys.argv[1:])
sys.exit(exit_code)
