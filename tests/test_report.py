import pytest

from simple_gpt.report import process_report, process_yaml


def test_small_report_generation(git_diff, small_report, mock_openai):
    """Test small report generation with mocks."""
    report_generation_test(git_diff, small_report)


@pytest.mark.integration
def test_int_small_report_generation(git_diff, small_report):
    """Test small report generation."""
    report_generation_test(git_diff, small_report)


def test_report_generation(git_diff, report_config):
    """Test report generation with mocks."""
    report_generation_test(git_diff, report_config)


@pytest.mark.integration
def test_int_report_generation(git_diff, report_config):
    """Test report generation."""
    report_generation_test(git_diff, report_config)


def test_process_yaml(git_diff, config_yaml, mock_openai):
    process_yaml_test(git_diff, config_yaml)


@pytest.mark.integration
def test_int_process_yaml(git_diff, config_yaml):
    process_yaml_test(git_diff, config_yaml)


def report_generation_test(git_diff, small_report):
    report = process_report(git_diff, small_report)
    assert report


def process_yaml_test(git_diff, config_yaml):
    """Test process_yaml."""
    report = process_yaml(git_diff, config_yaml)
    assert report
