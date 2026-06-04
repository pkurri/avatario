"""
AI Receptionist Workflow Engine
Handles pre-call, in-call, and post-call automation
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import asyncio
import uuid

class WorkflowTrigger(Enum):
    PRE_CALL = "pre_call"
    IN_CALL = "in_call"
    POST_CALL = "post_call"
    ON_ESCALATION = "on_escalation"
    ON_BOOKING = "on_booking"
    ON_ORDER = "on_order"

class ActionType(Enum):
    SEND_SMS = "send_sms"
    SEND_EMAIL = "send_email"
    SEND_WHATSAPP = "send_whatsapp"
    CREATE_CALENDAR_EVENT = "create_calendar_event"
    UPDATE_CRM = "update_crm"
    WEBHOOK = "webhook"
    WAIT = "wait"
    CONDITION = "condition"
    TRANSFER = "transfer"

@dataclass
class WorkflowAction:
    id: str
    type: ActionType
    config: Dict[str, Any] = field(default_factory=dict)
    conditions: List[Dict] = field(default_factory=list)
    on_error: str = "continue"  # continue, stop, retry
    retry_count: int = 3

@dataclass
class Workflow:
    id: str
    name: str
    trigger: WorkflowTrigger
    actions: List[WorkflowAction]
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

@dataclass
class CallContext:
    call_sid: str
    caller_number: str
    caller_name: Optional[str] = None
    persona_id: str = "anya"
    business_id: str = "default"
    transcript: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    crm_data: Dict[str, Any] = field(default_factory=dict)
    booking_data: Dict[str, Any] = field(default_factory=dict)

class WorkflowEngine:
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.action_handlers: Dict[ActionType, Callable] = {
            ActionType.SEND_SMS: self._handle_send_sms,
            ActionType.SEND_EMAIL: self._handle_send_email,
            ActionType.SEND_WHATSAPP: self._handle_send_whatsapp,
            ActionType.CREATE_CALENDAR_EVENT: self._handle_create_calendar,
            ActionType.UPDATE_CRM: self._handle_update_crm,
            ActionType.WEBHOOK: self._handle_webhook,
            ActionType.WAIT: self._handle_wait,
            ActionType.CONDITION: self._handle_condition,
            ActionType.TRANSFER: self._handle_transfer,
        }
        self.execution_log: List[Dict] = []
        
        # Initialize default workflows
        self._init_default_workflows()
    
    def _init_default_workflows(self):
        """Initialize default workflows for common use cases"""
        
        # Pre-call enrichment workflow
        self.create_workflow(Workflow(
            id="pre_call_enrichment",
            name="Pre-Call CRM Enrichment",
            trigger=WorkflowTrigger.PRE_CALL,
            actions=[
                WorkflowAction(
                    id="lookup_crm",
                    type=ActionType.UPDATE_CRM,
                    config={"operation": "lookup", "fields": ["name", "history", "preferences"]}
                ),
                WorkflowAction(
                    id="check_bookings",
                    type=ActionType.CREATE_CALENDAR_EVENT,
                    config={"operation": "check_upcoming", "caller_field": "caller_number"}
                ),
            ]
        ))
        
        # Post-call follow-up workflow
        self.create_workflow(Workflow(
            id="post_call_followup",
            name="Post-Call Follow-up",
            trigger=WorkflowTrigger.POST_CALL,
            actions=[
                WorkflowAction(
                    id="send_summary",
                    type=ActionType.SEND_EMAIL,
                    config={
                        "template": "call_summary",
                        "to": "{{caller_email}}",
                        "subject": "Summary of your call with {{business_name}}"
                    },
                    conditions=[{"field": "call_duration", "operator": ">", "value": 60}]
                ),
                WorkflowAction(
                    id="schedule_followup",
                    type=ActionType.WAIT,
                    config={"delay_hours": 24}
                ),
                WorkflowAction(
                    id="send_satisfaction_sms",
                    type=ActionType.SEND_SMS,
                    config={
                        "template": "satisfaction_survey",
                        "to": "{{caller_number}}",
                        "message": "How was your experience? Reply 1-5"
                    }
                ),
            ]
        ))
        
        # Booking confirmation workflow
        self.create_workflow(Workflow(
            id="booking_confirmation",
            name="Booking Confirmation",
            trigger=WorkflowTrigger.ON_BOOKING,
            actions=[
                WorkflowAction(
                    id="create_calendar",
                    type=ActionType.CREATE_CALENDAR_EVENT,
                    config={"calendar": "google", "send_invites": True}
                ),
                WorkflowAction(
                    id="send_whatsapp_confirm",
                    type=ActionType.SEND_WHATSAPP,
                    config={
                        "template": "appointment_confirmation",
                        "to": "{{caller_number}}",
                        "variables": ["{{booking_date}}", "{{booking_time}}"]
                    }
                ),
                WorkflowAction(
                    id="update_crm_booking",
                    type=ActionType.UPDATE_CRM,
                    config={"operation": "add_interaction", "type": "booking_created"}
                ),
            ]
        ))
        
        # Escalation workflow
        self.create_workflow(Workflow(
            id="escalation_handling",
            name="Escalation to Human",
            trigger=WorkflowTrigger.ON_ESCALATION,
            actions=[
                WorkflowAction(
                    id="notify_agent",
                    type=ActionType.SEND_SMS,
                    config={
                        "to": "{{agent_number}}",
                        "message": "Urgent: Call from {{caller_name}} ({{caller_number}}) needs attention. Reason: {{escalation_reason}}"
                    }
                ),
                WorkflowAction(
                    id="transfer_call",
                    type=ActionType.TRANSFER,
                    config={"queue": "support", "priority": "high", "timeout": 300}
                ),
                WorkflowAction(
                    id="log_escalation",
                    type=ActionType.UPDATE_CRM,
                    config={"operation": "add_note", "note": "Escalated: {{escalation_reason}}"}
                ),
            ]
        ))
    
    def create_workflow(self, workflow: Workflow) -> str:
        """Create a new workflow"""
        self.workflows[workflow.id] = workflow
        return workflow.id
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID"""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self, trigger: Optional[WorkflowTrigger] = None) -> List[Workflow]:
        """List all workflows, optionally filtered by trigger"""
        workflows = list(self.workflows.values())
        if trigger:
            workflows = [w for w in workflows if w.trigger == trigger]
        return workflows
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow"""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            return True
        return False
    
    async def execute_workflow(self, workflow_id: str, context: CallContext) -> Dict[str, Any]:
        """Execute a workflow with the given call context"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {"error": "Workflow not found"}
        
        if not workflow.enabled:
            return {"status": "skipped", "reason": "Workflow disabled"}
        
        execution_id = f"EXEC_{uuid.uuid4().hex[:12]}"
        results = []
        
        for action in workflow.actions:
            try:
                # Check conditions
                if action.conditions and not self._evaluate_conditions(action.conditions, context):
                    results.append({"action_id": action.id, "status": "skipped", "reason": "conditions_not_met"})
                    continue
                
                # Execute action
                handler = self.action_handlers.get(action.type)
                if handler:
                    result = await handler(action.config, context)
                    results.append({"action_id": action.id, "status": "success", "result": result})
                else:
                    results.append({"action_id": action.id, "status": "error", "reason": "no_handler"})
                    
            except Exception as e:
                error_result = {"action_id": action.id, "status": "error", "error": str(e)}
                results.append(error_result)
                
                if action.on_error == "stop":
                    break
                elif action.on_error == "retry" and action.retry_count > 0:
                    # Retry logic
                    for attempt in range(action.retry_count):
                        try:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            result = await handler(action.config, context)
                            error_result["status"] = "success"
                            error_result["result"] = result
                            error_result["retry_attempt"] = attempt + 1
                            break
                        except Exception as retry_error:
                            continue
        
        # Log execution
        execution_record = {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "call_sid": context.call_sid,
            "trigger": workflow.trigger.value,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.execution_log.append(execution_record)
        
        return {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "status": "completed",
            "actions_executed": len(results),
            "results": results
        }
    
    async def trigger_workflows(self, trigger: WorkflowTrigger, context: CallContext) -> List[Dict]:
        """Trigger all workflows matching the trigger type"""
        workflows = self.list_workflows(trigger)
        results = []
        
        for workflow in workflows:
            result = await self.execute_workflow(workflow.id, context)
            results.append(result)
        
        return results
    
    def _evaluate_conditions(self, conditions: List[Dict], context: CallContext) -> bool:
        """Evaluate if all conditions are met"""
        for condition in conditions:
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")
            
            # Get field value from context
            field_value = self._get_field_value(field, context)
            
            if operator == "==":
                if field_value != value:
                    return False
            elif operator == "!=":
                if field_value == value:
                    return False
            elif operator == ">":
                if not (field_value and field_value > value):
                    return False
            elif operator == "<":
                if not (field_value and field_value < value):
                    return False
            elif operator == "exists":
                if not field_value:
                    return False
            elif operator == "contains":
                if not (field_value and value in str(field_value)):
                    return False
        
        return True
    
    def _get_field_value(self, field: str, context: CallContext) -> Any:
        """Extract field value from context using dot notation"""
        parts = field.split(".")
        value = context
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None
        
        return value
    
    # Action Handlers
    
    async def _handle_send_sms(self, config: Dict, context: CallContext) -> Dict:
        """Handle SMS sending"""
        # TODO: Integrate with Twilio/SMS provider
        message = self._render_template(config.get("message", ""), context)
        to = self._render_template(config.get("to", ""), context)
        
        return {
            "channel": "sms",
            "to": to,
            "message": message,
            "status": "queued",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_send_email(self, config: Dict, context: CallContext) -> Dict:
        """Handle email sending"""
        # TODO: Integrate with SendGrid/AWS SES
        subject = self._render_template(config.get("subject", ""), context)
        body = self._render_template(config.get("body", ""), context)
        to = self._render_template(config.get("to", ""), context)
        
        return {
            "channel": "email",
            "to": to,
            "subject": subject,
            "status": "queued",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_send_whatsapp(self, config: Dict, context: CallContext) -> Dict:
        """Handle WhatsApp message sending"""
        # TODO: Integrate with WhatsApp Business API
        message = self._render_template(config.get("message", ""), context)
        to = self._render_template(config.get("to", ""), context)
        template = config.get("template")
        
        return {
            "channel": "whatsapp",
            "to": to,
            "template": template,
            "message": message,
            "status": "queued",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_create_calendar(self, config: Dict, context: CallContext) -> Dict:
        """Handle calendar event creation"""
        # TODO: Integrate with Google/Outlook Calendar
        operation = config.get("operation", "create")
        
        if operation == "create":
            return {
                "operation": "create_event",
                "calendar": config.get("calendar", "google"),
                "title": config.get("title", "Call with {{caller_name}}"),
                "start_time": context.booking_data.get("start_time"),
                "end_time": context.booking_data.get("end_time"),
                "attendees": [context.caller_number],
                "status": "created"
            }
        elif operation == "check_upcoming":
            return {
                "operation": "check_upcoming",
                "upcoming_events": [],  # TODO: Query calendar
                "status": "success"
            }
        
        return {"status": "unknown_operation"}
    
    async def _handle_update_crm(self, config: Dict, context: CallContext) -> Dict:
        """Handle CRM updates"""
        # TODO: Integrate with HubSpot/Salesforce
        operation = config.get("operation", "update")
        
        if operation == "lookup":
            # Simulate CRM lookup
            context.crm_data = {
                "customer_id": f"CUST_{context.caller_number[-8:]}",
                "name": "Unknown",  # Would be fetched from CRM
                "email": f"customer_{context.caller_number[-8:]}@example.com",
                "last_contact": None,
                "total_calls": 0,
                "tags": ["new_lead"]
            }
            return {"operation": "lookup", "found": True, "data": context.crm_data}
        
        elif operation == "add_interaction":
            return {
                "operation": "add_interaction",
                "type": config.get("type"),
                "call_sid": context.call_sid,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        elif operation == "add_note":
            return {
                "operation": "add_note",
                "note": config.get("note", ""),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {"status": "unknown_operation"}
    
    async def _handle_webhook(self, config: Dict, context: CallContext) -> Dict:
        """Handle webhook calls"""
        import aiohttp
        
        url = config.get("url", "")
        method = config.get("method", "POST")
        headers = config.get("headers", {})
        payload = config.get("payload", {})
        
        # Render templates in payload
        rendered_payload = {}
        for key, value in payload.items():
            if isinstance(value, str):
                rendered_payload[key] = self._render_template(value, context)
            else:
                rendered_payload[key] = value
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=rendered_payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    return {
                        "status": "success",
                        "status_code": response.status,
                        "response": await response.text()
                    }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _handle_wait(self, config: Dict, context: CallContext) -> Dict:
        """Handle wait/delay"""
        delay_hours = config.get("delay_hours", 0)
        delay_minutes = config.get("delay_minutes", 0)
        delay_seconds = config.get("delay_seconds", 0)
        
        total_seconds = (delay_hours * 3600) + (delay_minutes * 60) + delay_seconds
        
        # In real implementation, this would schedule a future task
        # For now, just simulate
        await asyncio.sleep(min(total_seconds, 5))  # Cap at 5 seconds for testing
        
        return {
            "status": "waited",
            "delay_seconds": total_seconds,
            "scheduled_for": (datetime.utcnow() + timedelta(seconds=total_seconds)).isoformat()
        }
    
    async def _handle_condition(self, config: Dict, context: CallContext) -> Dict:
        """Handle conditional branching"""
        condition = config.get("condition", {})
        if_true = config.get("if_true", [])
        if_false = config.get("if_false", [])
        
        is_true = self._evaluate_conditions([condition], context)
        
        return {
            "status": "evaluated",
            "result": is_true,
            "branch": "true" if is_true else "false"
        }
    
    async def _handle_transfer(self, config: Dict, context: CallContext) -> Dict:
        """Handle call transfer"""
        queue = config.get("queue", "default")
        priority = config.get("priority", "normal")
        timeout = config.get("timeout", 300)
        
        return {
            "status": "transfer_initiated",
            "queue": queue,
            "priority": priority,
            "timeout": timeout,
            "transfer_id": f"XFER_{uuid.uuid4().hex[:12]}"
        }
    
    def _render_template(self, template: str, context: CallContext) -> str:
        """Render template variables with context data"""
        variables = {
            "{{caller_number}}": context.caller_number,
            "{{caller_name}}": context.caller_name or "Valued Customer",
            "{{call_sid}}": context.call_sid,
            "{{persona_id}}": context.persona_id,
            "{{business_name}}": context.metadata.get("business_name", "Our Business"),
            "{{business_email}}": context.metadata.get("business_email", "support@example.com"),
            "{{caller_email}}": context.crm_data.get("email", ""),
            "{{booking_date}}": context.booking_data.get("date", ""),
            "{{booking_time}}": context.booking_data.get("time", ""),
            "{{agent_number}}": context.metadata.get("agent_number", ""),
            "{{escalation_reason}}": context.metadata.get("escalation_reason", ""),
        }
        
        result = template
        for var, value in variables.items():
            result = result.replace(var, str(value))
        
        return result
    
    def get_execution_history(self, call_sid: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get workflow execution history"""
        history = self.execution_log
        
        if call_sid:
            history = [e for e in history if e.get("call_sid") == call_sid]
        
        return history[-limit:]


# Global workflow engine instance
workflow_engine = WorkflowEngine()

async def test_workflow_engine():
    """Test the workflow engine"""
    engine = WorkflowEngine()
    
    # Create test context
    context = CallContext(
        call_sid="CALL_TEST123",
        caller_number="+919876543210",
        caller_name="John Doe",
        persona_id="anya",
        booking_data={
            "date": "2026-05-10",
            "time": "14:30",
            "service": "Consultation"
        }
    )
    
    # Test pre-call workflow
    print("Testing pre-call workflow...")
    result = await engine.trigger_workflows(WorkflowTrigger.PRE_CALL, context)
    print(f"Pre-call result: {json.dumps(result, indent=2)}")
    
    # Test booking workflow
    print("\nTesting booking workflow...")
    result = await engine.trigger_workflows(WorkflowTrigger.ON_BOOKING, context)
    print(f"Booking result: {json.dumps(result, indent=2)}")
    
    # Print execution history
    print("\nExecution history:")
    history = engine.get_execution_history()
    for entry in history:
        print(f"  - {entry['execution_id']}: {entry['workflow_id']} ({entry['timestamp']})")

if __name__ == "__main__":
    asyncio.run(test_workflow_engine())
