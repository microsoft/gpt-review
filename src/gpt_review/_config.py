"""Utils for processing YAML config files."""
import yaml

from gpt_review._review import _request_goal


def process_yaml(git_diff, yaml_file: str) -> str:
    """
    Load YAML formatted string and create report.

    Args:
        git_diff (str): The git diff to split.
        yaml_file (str): The YAML contents to process.

    Returns:
        str: The report.
    """
    config = yaml.safe_load(yaml_file)
    report = config["report"]
    return process_report(git_diff, report)


def process_report(git_diff, report: dict, indent="#") -> str:
    """
    for-each record in report
    - if record is a string, check_goals
    - else recursively call process_report
    """
    return "".join(
        f"""
{indent} {key}

{_request_goal(git_diff, goal=record)}
"""
        if isinstance(record, str)
        else process_report(git_diff, record, indent=f"{indent}#")
        for key, record in report.values()
    )
