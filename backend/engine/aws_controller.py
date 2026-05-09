import logging
import boto3
import os
from typing import Dict
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

logger = logging.getLogger(__name__)

# Configuration
REGION = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "ap-south-1"
INSTANCE_ID = os.getenv("LLM_INSTANCE_ID") or os.getenv("AWS_LLM_INSTANCE_ID")


def _missing_config() -> Dict[str, str] | None:
    if not INSTANCE_ID:
        return {
            "status": "error",
            "message": "Missing LLM_INSTANCE_ID or AWS_LLM_INSTANCE_ID environment variable.",
        }
    return None

def get_ec2_client():
    return boto3.client('ec2', region_name=REGION)

async def get_llm_instance_status() -> Dict[str, str]:
    """
    Checks the current status of the Nyayamitra LLM instance.
    Returns: {'status': 'pending'|'running'|'shutting-down'|'terminated'|'stopping'|'stopped'}
    """
    missing = _missing_config()
    if missing:
        return missing

    try:
        ec2 = get_ec2_client()
        response = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
        state = response['Reservations'][0]['Instances'][0]['State']['Name']
        return {"status": state, "region": REGION, "instance_id": INSTANCE_ID}
    except (NoCredentialsError, PartialCredentialsError):
        return {
            "status": "error",
            "message": "AWS credentials not found. Configure AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY or an AWS profile/role with EC2 describe/start permissions.",
            "region": REGION,
            "instance_id": INSTANCE_ID,
        }
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "ClientError")
        message = e.response.get("Error", {}).get("Message", str(e))
        logger.error(f"Error checking EC2 status [{code}]: {message}")
        return {"status": "error", "message": f"{code}: {message}", "region": REGION, "instance_id": INSTANCE_ID}
    except Exception as e:
        logger.error(f"Error checking EC2 status: {e}")
        return {"status": "error", "message": str(e), "region": REGION, "instance_id": INSTANCE_ID}

async def start_llm_instance() -> Dict[str, str]:
    """
    Triggers the start of the Nyayamitra LLM instance.
    """
    missing = _missing_config()
    if missing:
        return missing

    try:
        ec2 = get_ec2_client()
        # Check current status first to avoid unnecessary calls
        current = await get_llm_instance_status()
        if current["status"] == "error":
            return current

        if current['status'] == 'running':
            return {"status": "running", "message": "Instance is already running."}
        
        if current['status'] == 'pending':
            return {"status": "pending", "message": "Instance is already starting."}

        ec2.start_instances(InstanceIds=[INSTANCE_ID])
        return {"status": "starting", "message": "Start signal sent to instance.", "region": REGION, "instance_id": INSTANCE_ID}
    except (NoCredentialsError, PartialCredentialsError):
        return {
            "status": "error",
            "message": "AWS credentials not found. Configure AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY or an AWS profile/role with EC2 describe/start permissions.",
            "region": REGION,
            "instance_id": INSTANCE_ID,
        }
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "ClientError")
        message = e.response.get("Error", {}).get("Message", str(e))
        logger.error(f"Error starting EC2 instance [{code}]: {message}")
        return {"status": "error", "message": f"{code}: {message}", "region": REGION, "instance_id": INSTANCE_ID}
    except Exception as e:
        logger.error(f"Error starting EC2 instance: {e}")
        return {"status": "error", "message": str(e), "region": REGION, "instance_id": INSTANCE_ID}
