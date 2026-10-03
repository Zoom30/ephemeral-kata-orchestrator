# Ephemeral Kata Orchestrator

A self-destructing AWS sandbox designed for backend engineers to practice infrastructure-as-code (IaC) and system design without the fear of surprise cloud bills. Deploy your complex backend stacks, practice your skills, and let the orchestrator tear it all down automatically when your time is up.

## Key Features

* **Zero Surprise Bills:** Automatically deletes the entire CloudFormation stack after a designated time window.

* **100% Python Native:** Infrastructure and Lambda logic written entirely in Python using AWS CDK and Boto3.

* **Event-Driven Teardown:** Uses EventBridge to detect deployment completion and trigger the countdown.

* **Modular "Kata" Sandbox:** Swap out the practice payload with any AWS architecture you want to learn.

## Architecture Breakdown

The project is split into two logical halves: the infrastructure you are practicing on, and the safety net that destroys it.

### 1. The "Kata" Payload (Your Practice Sandbox)

* **Amazon VPC:** Fully isolated network with private subnets.

* **Amazon API Gateway:** RESTful entry point for the sandbox API.

* **AWS Lambda:** Python compute layer utilizing **Pydantic** for rigorous JSON schema validation.

* **Amazon DynamoDB:** NoSQL data store.

* **VPC Endpoints (PrivateLink):** Allows the private Lambda to communicate securely with DynamoDB without traversing the public internet.

### 2. The Ephemeral Wrapper (The Self-Destruct Mechanism)

* **Amazon EventBridge:** Listens for the `CREATE_COMPLETE` CloudFormation event for this specific stack.

* **AWS Step Functions:** A state machine acting as a timer (e.g., holding a `Wait` state for 4 hours).

* **Terminator Lambda:** A Python/Boto3 function with scoped IAM permissions that calls `cloudformation:DeleteStack` to cleanly wipe the environment.

## Prerequisites

Ensure you have the following installed and configured before starting:

* [AWS CLI](https://aws.amazon.com/cli/) configured with your credentials.

* [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html) (Node.js required for the CDK CLI).

* [Python 3.9+](https://www.python.org/downloads/).

* [Docker](https://www.docker.com/) (Optional, but recommended if building Lambda layers).

## Getting Started

### 1. Clone and Setup

* Clone the repository: `git clone https://github.com/yourusername/ephemeral-kata-orchestrator.git`

* Navigate to the directory: `cd ephemeral-kata-orchestrator`

* Create a virtual environment: `python -m venv .venv`

* Activate the environment:

  * MacOS/Linux: `source .venv/bin/activate`

  * Windows: `.venv\Scripts\activate.bat`

* Install dependencies: `pip install -r requirements.txt`

### 2. Configure the Timer

* Open `app.py` or your main stack file.

* Locate the `Step Functions Wait State` configuration.

* Adjust the `duration` to your preferred practice window (default is 4 hours).

### 3. Deploy

* Bootstrap your AWS environment (if you haven't used CDK in this region before): `cdk bootstrap`

* Deploy the stack: `cdk deploy`

* Review the IAM changes and confirm with `y`.

## The Lifecycle (How it works)

1. **Deploy:** You run `cdk deploy`.

2. **Listen:** EventBridge detects the stack deployment success.

3. **Tick-Tock:** Step Functions starts the countdown.

4. **Practice:** You test, break, and iterate on the API/VPC sandbox.

5. **Terminate:** The timer hits zero, triggering the Terminator Lambda.

6. **Clean Slate:** The stack is deleted; your AWS bill remains safe.

## Extending the Sandbox

Want to practice something else?

* Simply remove the API Gateway/DynamoDB resources inside the `KataPayload` construct.

* Replace them with ECS Clusters, SQS Queues, or SageMaker endpoints.

* The Ephemeral Wrapper will still track the stack ID and delete whatever you build.
