from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    ticket_id: str
    customer_id: Optional[str]
    ticket_text: str
    intent: Optional[str]
    urgency: Optional[str]
    sentiment: Optional[str]
    extracted_entities: Dict[str, Any]
    triage_confidence: float
    policy_citation: Optional[str]
    policy_decision: Optional[str]
    policy_reasoning: Optional[str]
    planned_actions: List[Dict[str, Any]]
    execution_results: List[Dict[str, Any]]
    requires_approval: bool
    approval_status: Optional[str]
    is_escalated: bool
    escalation_summary: Optional[str]
    final_reply: Optional[str]
    messages: List[Any]