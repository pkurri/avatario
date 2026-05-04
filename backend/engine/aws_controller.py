import boto3
import os
from typing import Dict

# Configuration
REGION = "ap-south-1"
INSTANCE_ID = "i-0d58636add0780606"

def get_ec2_client():
    return boto3.client('ec2', region_name=REGION)

async def get_llm_instance_status() -> Dict[str, str]:
    """
    Checks the current status of the Nyayamitra LLM instance.
    Returns: {'status': 'pending'|'running'|'shutting-down'|'terminated'|'stopping'|'stopped'}
    """
    try:
        ec2 = get_ec2_client()
        response = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
        state = response['Reservations'][0]['Instances'][0]['State']['Name']
        return {"status": state}
    except Exception as e:
        print(f"Error checking EC2 status: {e}")
        return {"status": "error", "message": str(e)}

async def start_llm_instance() -> Dict[str, str]:
    """
    Triggers the start of the Nyayamitra LLM instance.
    """
    try:
        ec2 = get_ec2_client()
        # Check current status first to avoid unnecessary calls
        current = await get_llm_instance_status()
        if current['status'] == 'running':
            return {"status": "running", "message": "Instance is already running."}
        
        if current['status'] == 'pending':
            return {"status": "pending", "message": "Instance is already starting."}

        ec2.start_instances(InstanceIds=[INSTANCE_ID])
        return {"status": "starting", "message": "Start signal sent to instance."}
    except Exception as e:
        print(f"Error starting EC2 instance: {e}")
        return {"status": "error", "message": str(e)}
