"""Azure DevOps API incoming message handler."""
import os

import azure.functions as func

from gpt_review.repositories.devops import DevOpsFunction

HANDLER = DevOpsFunction(
    pat=os.environ["ADO_TOKEN"],
    org=os.environ["ADO_ORG"],
    project=os.environ["ADO_PROJECT"],
    repository_id=os.environ["ADO_REPO"],
)

os.putenv("RISK_SUMMARY", "false")
os.putenv("FILE_SUMMARY_FULL", "false")
os.putenv("TEST_SUMMARY", "false")
os.putenv("BUG_SUMMARY", "false")
os.putenv("SUMMARY_SUGGEST", "false")


def main(msg: func.ServiceBusMessage) -> None:
    """Handle an incoming message."""
    HANDLER.handle(msg)
