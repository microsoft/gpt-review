import os
import sys


from knack import CLI, CLICommandsLoader


from easy_gpt import __version__
CLI_NAME = "gpt"


class GPTCLI(CLI):
    """Custom CLI implemntation to set version for the GPT CLI."""

    def get_cli_version(self):
        return __version__


class GPTCommandsLoader(CLICommandsLoader):
    """The GPT CLI Commands Loader."""

    def load_command_table(self, args):
        AskCommandGroup.load_command_table(self)
        GitCommandGroup.load_command_table(self)
        return OrderedDict(self.command_table)

    def load_arguments(self, command):
        AskCommandGroup.load_arguments(self)
        super(GPTCommandsLoader, self).load_arguments(command)


def cli() -> int:
    """The GPT CLI entry point."""
    gpt = GPTCLI(
        cli_name=CLI_NAME,
        config_dir=os.path.expanduser(os.path.join("~", f".{CLI_NAME}")),
        config_env_var_prefix=CLI_NAME,
        commands_loader_cls=GPTCommandsLoader,
    )
    return gpt.invoke(sys.argv[1:])
