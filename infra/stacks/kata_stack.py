from aws_cdk import (
    Stack,
)
from constructs import Construct

from infra.constructs_lib.cleanup_construct import CleanupConstruct


class EphemeralKataOrchestratorStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        CleanupConstruct(self, "CleanupConstruct", stack_id=self.stack_id)
