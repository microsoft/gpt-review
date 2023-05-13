"""Utility functions"""
import logging
import time

import gpt_review.constants as C


def retry_with_exponential_backoff(retry_count, retry_after):
    """Use exponential backoff to retry a request after specific time while staying under the retry count"""
    logging.warning("Call to GPT failed due to rate limit, retry attempt %s of %s", retry_count, C.MAX_RETRIES)

    wait_time = int(
        int(retry_after) * 2 * (1 + retry_count / C.MAX_RETRIES)
        if retry_after
        else retry_count * 2 * (1 + retry_count / C.MAX_RETRIES)
    )

    logging.warning("Waiting for %s seconds before retrying.", wait_time)

    time.sleep(wait_time)
