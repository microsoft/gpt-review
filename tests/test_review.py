import pytest

from gpt_review._review import get_review


def test_get_review(mock_openai) -> None:
    get_review_test()


@pytest.mark.integration
def test_int_get_review() -> None:
    get_review_test()


def get_review_test() -> None:
    """Test get_review."""
    get_review(
        """
diff --git a/README.md b/README.md
index 6d0d0a7..b2b0b0a 100644
--- a/README.md
+++ b/README.md
@@ -1,4 +1,4 @@
-# GPT Review
+# GPT Review Test
    GPT Review is a tool to help with code reviews.
    It uses GPT-4 to summarize code changes and provide insights.
    It is currently in alpha.
diff --git a/src/gpt_review/_ask.py b/src/gpt_review/_ask.py
index 6d0d0a7..b2b0b0a 100644
--- a/src/gpt_review/_ask.py
+++ b/src/gpt_review/_ask.py
@@ -1,4 +1,4 @@
-# GPT Review
+# GPT Review Test
    GPT Review is a tool to help with code reviews.
    It uses GPT-4 to summarize code changes and provide insights.
    It is currently in alpha.
"""
    )
