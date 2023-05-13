"""Utility functions"""
import logging
import time
from typing import Optional

import gpt_review.constants as C


def retry_with_exponential_backoff(current_retry: int, retry_after: Optional[str]) -> None:
    """
    Use exponential backoff to retry a request after specific time while staying under the retry count

    Args:
        current_retry (int): The current retry count.
        retry_after (Optional[str]): The time to wait before retrying.
    """
    logging.warning("Call to GPT failed due to rate limit, retry attempt %s of %s", current_retry, C.MAX_RETRIES)

    wait_time = int(
        int(retry_after) * 2 * (1 + current_retry / C.MAX_RETRIES)
        if retry_after
        else current_retry * 2 * (1 + current_retry / C.MAX_RETRIES)
    )

    logging.warning("Waiting for %s seconds before retrying.", wait_time)

    time.sleep(wait_time)
