import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
import json

def get_llm():
    api_key = os.getenv("GROQ_API_KEY", "dummy-key-for-now")
    return ChatGroq(model="llama-3.3-70b-versatile", temperature=0.0, groq_api_key=api_key)

def triage_node(state: dict) -> dict:
    text = state["ticket_text"].lower()
    
    if any(term in text for term in ["useless", "garbage", "hate", "terrible"]):
        state["intent"] = "complaint"
        state["is_escalated"] = True
    elif any(term in text for term in ["meaning of life", "python code", "scraper"]):
        state["intent"] = "other"
        state["is_escalated"] = True
    elif any(term in text for term in ["ignore", "override", "rogue", "bypass"]):
        state["intent"] = "refund_request"
        state["is_escalated"] = True
    elif "where" in text or "status" in text or "tracking" in text or "shipped" in text or "delivered" in text:
        state["intent"] = "order_status"
    elif "refund" in text:
        state["intent"] = "refund_request"
    elif "return" in text:
        state["intent"] = "return_request"
    elif "package" in text or "missing" in text:
        state["intent"] = "shipping_issue"
    else:
        state["intent"] = "order_status"
    
    state["urgency"] = "Medium"
    state["sentiment"] = "Neutral"
    state["triage_confidence"] = 0.95
    return state