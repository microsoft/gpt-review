"""Utility functions for simple_gpt."""


def chunks(string, length):
    """Split a string into chunks of a given length.

    Args:
        string (str): The string to split.
        length (int): The length of the chunks.

    Yields:
        str: A chunk of the string.
    """
    for start in range(0, len(string), length):
        yield string[start : start + length]


def splits(string):
    """Split a string into chunks of 3000 characters.

    Args:
        string (str): The string to split.

    Yields:
        str: A chunk of the string.
    """
    for commit in string.split("From: "):
        # for split in commit.split("diff"):
        yield chunks(commit, 3000)
