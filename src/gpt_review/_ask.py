"""Ask GPT a question."""
import logging
from typing import Dict, List, Optional

from knack import CLICommandsLoader
from knack.arguments import ArgumentsContext
from knack.commands import CommandGroup
from knack.util import CLIError

import gpt_review.constants as C
from gpt_review._command import GPTCommandGroup
from gpt_review._llama_index import _query_index
from gpt_review._openai import _call_gpt
from gpt_review.context import _load_azure_openai_context


def validate_parameter_range(namespace) -> None:
    """
    Validate the following parameters:
    - max_tokens is in [1,4000]
    - temperature is in [0,1]
    - top_p is in [0,1]
    - frequency_penalty is in [0,2]
    - presence_penalty is in [0,2]

    Args:
        namespace (argparse.Namespace): The namespace to validate.

    Raises:
        CLIError: If the parameter is not within the allowed range.
    """
    _range_validation(namespace.max_tokens, "max-tokens", C.MAX_TOKENS_MIN, C.MAX_TOKENS_MAX)
    _range_validation(namespace.temperature, "temperature", C.TEMPERATURE_MIN, C.TEMPERATURE_MAX)
    _range_validation(namespace.top_p, "top-p", C.TOP_P_MIN, C.TOP_P_MAX)
    _range_validation(
        namespace.frequency_penalty, "frequency-penalty", C.FREQUENCY_PENALTY_MIN, C.FREQUENCY_PENALTY_MAX
    )
    _range_validation(namespace.presence_penalty, "presence-penalty", C.PRESENCE_PENALTY_MIN, C.PRESENCE_PENALTY_MAX)


def _range_validation(param, name, min_value, max_value) -> None:
    """Validates that the given parameter is within the allowed range

    Args:
        param (int or float): The parameter value to validate.
        name (str): The name of the parameter.
        min_value (int or float): The minimum allowed value for the parameter.
        max_value (int or float): The maximum allowed value for the parameter.

    Raises:
        CLIError: If the parameter is not within the allowed range.
    """
    if param is not None and (param < min_value or param > max_value):
        raise CLIError(f"--{name} must be a(n) {type(param).__name__} between {min_value} and {max_value}")


def _ask(
    question: List[str],
    max_tokens: int = C.MAX_TOKENS_DEFAULT,
    temperature: float = C.TEMPERATURE_DEFAULT,
    top_p: float = C.TOP_P_DEFAULT,
    frequency_penalty: float = C.FREQUENCY_PENALTY_DEFAULT,
    presence_penalty: float = C.PRESENCE_PENALTY_DEFAULT,
    files: Optional[List[str]] = None,
    messages=None,
    fast: bool = False,
    large: bool = False,
    directory: Optional[str] = None,
    reset: bool = False,
    required_exts: Optional[List[str]] = None,
    hidden: bool = False,
    recursive: bool = False,
    repository: Optional[str] = None,
    branch: str = "main",
) -> Dict[str, str]:
    """
    Ask GPT a question.

    Args:
        question (List[str]): The question to ask GPT.
        max_tokens (int, optional): The maximum number of tokens to generate. Defaults to C.MAX_TOKENS_DEFAULT.
        temperature (float, optional): Controls randomness. Defaults to C.TEMPERATURE_DEFAULT.
        top_p (float, optional): Controls diversity via nucleus sampling. Defaults to C.TOP_P_DEFAULT.
        frequency_penalty (float, optional): How much to penalize new tokens based on their existing frequency in the
            text so far. Defaults to C.FREQUENCY_PENALTY_DEFAULT.
        presence_penalty (float, optional): How much to penalize new tokens based on whether they appear in the text so
            far. Defaults to C.PRESENCE_PENALTY_DEFAULT.
        files (Optional[List[str]], optional): The files to search. Defaults to None.
        messages ([type], optional): [description]. Defaults to None.
        fast (bool, optional): Use the fast model. Defaults to False.
        large (bool, optional): Use the large model. Defaults to False.
        directory (Optional[str], optional): The directory to search. Defaults to None.
        reset (bool, optional): Whether to reset the index. Defaults to False.
        required_exts (Optional[List[str]], optional): The required file extensions. Defaults to None.
        hidden (bool, optional): Include hidden files. Defaults to False.
        recursive (bool, optional): Recursively search the directory. Defaults to False.
        repository (Optional[str], optional): The repository to search. Defaults to None.

    Returns:
            Dict[str, str]: The response from GPT.
    """
    _load_azure_openai_context()

    prompt = "".join(question)

    if files or directory or repository:
        response = _query_index(
            prompt,
            files,
            input_dir=directory,
            reset=reset,
            exclude_hidden=not hidden,
            recursive=recursive,
            required_exts=required_exts,
            repository=repository,
            branch=branch,
            fast=fast,
            large=large,
        )
    else:
        response = _call_gpt(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            fast=fast,
            large=large,
            messages=messages,
        )
    logging.info(response)
    return {"response": response}


class AskCommandGroup(GPTCommandGroup):
    """Ask Command Group."""

    @staticmethod
    def load_command_table(loader: CLICommandsLoader) -> None:
        with CommandGroup(loader, "", "gpt_review._ask#{}") as group:
            group.command("ask", "_ask", is_preview=True)

    @staticmethod
    def load_arguments(loader: CLICommandsLoader) -> None:
        with ArgumentsContext(loader, "ask") as args:
            args.positional("question", type=str, nargs="+", help="Provide a question to ask GPT.")
            args.argument(
                "fast",
                help="Use gpt-35-turbo for prompts < 4000 tokens.",
                default=False,
                action="store_true",
            )
            args.argument(
                "large",
                help="Use gpt-4-32k for prompts.",
                default=False,
                action="store_true",
            )
            args.argument(
                "temperature",
                type=float,
                help="Sets the level of creativity/randomness.",
                validator=validate_parameter_range,
            )
            args.argument(
                "max_tokens",
                type=int,
                help="The maximum number of tokens to generate.",
                validator=validate_parameter_range,
            )
            args.argument(
                "top_p",
                type=float,
                help="Also sets the level of creativity/randomness. Adjust temperature or top p but not both.",
                validator=validate_parameter_range,
            )
            args.argument(
                "frequency_penalty",
                type=float,
                help="Reduce the chance of repeating a token based on current frequency in the text.",
                validator=validate_parameter_range,
            )
            args.argument(
                "presence_penalty",
                type=float,
                help="Reduce the chance of repeating any token that has appeared in the text so far.",
                validator=validate_parameter_range,
            )
            args.argument(
                "files",
                type=str,
                help="Ask question about a file. Can be used multiple times.",
                default=None,
                action="append",
                options_list=("--files", "-f"),
            )
            args.argument(
                "directory",
                type=str,
                help="Path of the directory to index. Use --recursive (or -r) to index subdirectories.",
                default=None,
                options_list=("--directory", "-d"),
            )
            args.argument(
                "required_exts",
                type=str,
                help="Required extensions when indexing a directory. Requires --directory. Can be used multiple times.",
                default=None,
                action="append",
            )
            args.argument(
                "hidden",
                help="Include hidden files when indexing a directory. Requires --directory.",
                default=False,
                action="store_true",
            )
            args.argument(
                "recursive",
                help="Recursively index a directory. Requires --directory.",
                default=False,
                action="store_true",
                options_list=("--recursive", "-r"),
            )
            args.argument(
                "repository",
                type=str,
                help="Repository to index. Default: None.",
                default=None,
                options_list=("--repository", "-repo"),
            )
            args.argument(
                "branch",
                type=str,
                help="Branch to index. Default: main.",
                default="main",
                options_list=("--branch", "-b"),
            )
            args.argument(
                "reset",
                help="Reset the index, overwriting the directory. Requires --directory, --files, or --repository.",
                default=False,
                action="store_true",
            )
