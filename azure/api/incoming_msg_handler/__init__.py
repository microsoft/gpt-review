"""Azure DevOps API incoming message handler."""
import os
from gpt_review.repositories.devops import _DevOpsClient

import azure.functions as func


CLIENT = _DevOpsClient(
    pat=os.environ["ADO_TOKEN"],
    org=os.environ["ADO_ORG"],
    project=os.environ["ADO_PROJECT"],
    repository_id=os.environ["ADO_REPO"],
)


def main(msg: func.ServiceBusMessage) -> None:
    """Handle an incoming message."""
    CLIENT.handle(msg)
