from aws_cdk import (
    aws_stepfunctions_tasks as tasks, Duration,
    aws_events_targets as targets,
    aws_events as events,
    aws_iam as iam,
    aws_stepfunctions as sfn, RemovalPolicy,
aws_lambda as _lambda,
aws_logs as logs
)

from constructs import Construct

from infra.utilities.utils import build_lambda_code


class CleanupConstruct(Construct):
    def __init__(self, scope: "Construct", construct_id: str, **kwargs):
        super().__init__(scope, construct_id)


        self._lambda_code = build_lambda_code()

        wait = sfn.Wait(
            self, "WaitDuration", time=sfn.WaitTime.duration(Duration.hours(4))
        )

        cleanup_lambda = self.make_function(
            "CleanupLambda", handler="src.lambda.cleanup_lambda.handler"
        )
        cleanup = tasks.LambdaInvoke(
            self,
            "InvokeCleanup",
            lambda_function=cleanup_lambda,
        )

        timer = sfn.StateMachine(
            self,
            "CleanupTimer",
            state_machine_type=sfn.StateMachineType.STANDARD,
            definition_body=sfn.DefinitionBody.from_chainable(wait.next(cleanup)),
        )

        cf_listen_rule = events.Rule(
            self,
            "StackDeployedRule",
            event_pattern=events.EventPattern(
                source=["aws.cloudformation"],
                detail_type=["CloudFormation Stack Status Change"],
                detail={
                    "stack-id": [kwargs['stack_id']],
                    "status-details": {
                        "status": ["CREATE_COMPLETE", "UPDATE_COMPLETE"]
                    },
                },
            ),
        )
        cf_listen_rule.add_target(targets.SfnStateMachine(timer))
        cleanup_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudformation:DeleteStack"], resources=[kwargs['stack_id']]
            )
        )

    def make_function(
            self,
            function_id: str,
            *,
            handler: str,
            environment: dict[str, str] | None = None,
            timeout: Duration | None = None,
    ) -> _lambda.Function:
        return _lambda.Function(
            self,
            function_id,
            runtime=_lambda.Runtime.PYTHON_3_13,
            architecture=_lambda.Architecture.X86_64,
            handler=handler,
            code=self._lambda_code,
            environment=environment,
            memory_size=256,
            timeout=timeout or Duration.seconds(10),
            log_group=logs.LogGroup(
                self,
                f"{function_id}Logs",
                retention=logs.RetentionDays.ONE_WEEK,
                removal_policy=RemovalPolicy.DESTROY,
            ),
        )
