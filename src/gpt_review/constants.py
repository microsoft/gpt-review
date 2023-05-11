"""Contains constants for minimum and maximum values of various parameters used in GPT Review."""
import os
import sys

MAX_TOKENS_DEFAULT = 100
MAX_TOKENS_MIN = 1
MAX_TOKENS_MAX = sys.maxsize

TEMPERATURE_DEFAULT = 0.7
TEMPERATURE_MIN = 0
TEMPERATURE_MAX = 1

TOP_P_DEFAULT = 0.5
TOP_P_MIN = 0
TOP_P_MAX = 1

FREQUENCY_PENALTY_DEFAULT = 0.5
FREQUENCY_PENALTY_MIN = 0
FREQUENCY_PENALTY_MAX = 2

PRESENCE_PENALTY_DEFAULT = 0
PRESENCE_PENALTY_MIN = 0
PRESENCE_PENALTY_MAX = 2

MAX_RETRIES = int(os.getenv("MAX_RETRIES", 15))

BUG_PROMPT_YAML = os.getenv("BUG_PROMPT", "prompt_bug.yaml")
COVERAGE_PROMPT_YAML = os.getenv("COVERAGE_PROMPT", "prompt_coverage.yaml")
SUMMARY_PROMPT_YAML = os.getenv("SUMMARY_PROMPT", "prompt_summary.yaml")
