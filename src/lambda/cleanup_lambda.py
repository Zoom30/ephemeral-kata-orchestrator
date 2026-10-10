from loguru import logger
import boto3


cloudformation = boto3.client("cloudformation")


def handler(event, context):
    logger.info(f"even: {event}")
    stack_id = event["detail"]["stack-id"]
    cloudformation.delete_stack(StackName=stack_id)
    logger.info(f"context: {context}")
