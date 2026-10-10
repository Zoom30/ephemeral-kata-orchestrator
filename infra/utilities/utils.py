import shutil
import subprocess
from pathlib import Path

import jsii
from aws_cdk import (
    BundlingOptions,
    ILocalBundling,
    aws_lambda as _lambda,
)

CODE_EXCLUDES = [
    ".venv/**",
    "cdk.out/**",
    ".git/**",
    "**/__pycache__/**",
    "**/*.pyc",
    "**/*.pyo",
    "infra/**",
    "tests/**",
]

REPO_ROOT = Path(__file__).resolve().parents[2]

# Wheel tags for the Lambda functions' architecture (Architecture.X86_64,
# Runtime.PYTHON_3_13). Kept as wheel-selection flags rather than an
# --platform Docker pin so builds run with the host's own pip on any dev
# machine (Apple Silicon included) without cross-arch emulation.
LAMBDA_PIP_PLATFORM = "manylinux2014_x86_64"
LAMBDA_PIP_PYTHON_VERSION = "3.13"
LAMBDA_PIP_ABI = "cp313"


@jsii.implements(ILocalBundling)
class _PipLocalBundling:
    """Installs Lambda deps with the host's pip instead of Docker.

    `--platform`/`--abi`/`--only-binary=:all:` make pip select prebuilt
    wheels tagged for Lambda's target regardless of host arch/OS, so no
    code for the target architecture is ever executed locally. Falls back
    to the Docker bundling defined in `build_lambda_code` (by returning
    False) if that ever isn't possible, e.g. a dependency with no
    prebuilt wheel for this target.
    """

    def try_bundle(self, output_dir: str, *args, **kwargs) -> bool:
        try:
            subprocess.run(
                [
                    "pip",
                    "install",
                    "--no-cache-dir",
                    "--only-binary=:all:",
                    "--platform",
                    LAMBDA_PIP_PLATFORM,
                    "--python-version",
                    LAMBDA_PIP_PYTHON_VERSION,
                    "--implementation",
                    "cp",
                    "--abi",
                    LAMBDA_PIP_ABI,
                    "-r",
                    str(REPO_ROOT / "requirements.txt"),
                    "-t",
                    output_dir,
                ],
                cwd=REPO_ROOT,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

        shutil.copytree(REPO_ROOT / "src", Path(output_dir) / "src")
        return True


def build_lambda_code() -> _lambda.Code:
    """Package src/ together with its runtime dependencies (not CDK/dev tooling) for Lambda.

    `Code.from_asset` alone only zips up our own source, so third-party
    packages like loguru/pydantic never made it into the deployment package
    and every Lambda failed with Runtime.ImportModuleError. Exporting only
    the default uv dependency groups (excluding the "dev" and "infra"
    groups) keeps aws-cdk-constructs_lib/jsii/type-stubs out of the bundle.
    """
    requirements_path = REPO_ROOT / "requirements.txt"
    subprocess.run(
        [
            "uv",
            "export",
            "--frozen",
            "--no-hashes",
            "--no-emit-project",
            "--no-default-groups",
            "-o",
            str(requirements_path),
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    return _lambda.Code.from_asset(
        path=str(REPO_ROOT),
        exclude=CODE_EXCLUDES,
        bundling=BundlingOptions(
            image=_lambda.Runtime.PYTHON_3_13.bundling_image,
            local=_PipLocalBundling(),
            # Pin to amd64 so pip fetches x86_64 wheels for native extensions
            # (e.g. pydantic_core). Must match the Lambda functions' architecture.
            # Only used as a fallback if _PipLocalBundling can't run.
            platform="linux/amd64",
            command=[
                "bash",
                "-c",
                "pip install --no-cache-dir -r requirements.txt -t /asset-output "
                "&& cp -r src /asset-output/src",
            ],
        ),
    )
