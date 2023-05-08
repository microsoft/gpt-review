"""Tests for customized markdown report generation."""
import pytest

from gpt_review._review import _process_report, _process_yaml


def test_report_generation(git_diff, report_config, mock_openai) -> None:
    """Test report generation with mocks."""
    report_generation_test(git_diff, report_config)


@pytest.mark.integration
def test_int_report_generation(git_diff, report_config) -> None:
    """Test report generation."""
    report_generation_test(git_diff, report_config)


def test_process_yaml(git_diff, config_yaml, mock_openai) -> None:
    process_yaml_test(git_diff, config_yaml)


@pytest.mark.integration
def test_int_process_yaml(git_diff, config_yaml) -> None:
    process_yaml_test(git_diff, config_yaml)


def report_generation_test(git_diff, report_config) -> None:
    report = _process_report(git_diff, report_config)
    assert report


def process_yaml_test(git_diff, config_yaml) -> None:
    """Test process_yaml."""
    report = _process_yaml(git_diff, config_yaml)
    assert report
