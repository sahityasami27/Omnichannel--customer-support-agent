import re
import uuid
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database import engine, Base, get_db
from backend.app.models import CustomerModel, OrderModel, ShipmentModel
from backend.app.tools import router as tools_router
from backend.app.voice import router as voice_router
from backend.app.auth import (
    AuthContext,
    get_auth_context,
    require_admin,
    USER_CREDENTIALS,
    verify_password,
    create_access_token,
)
from backend.data.seed_data import init_db
from backend.agent.graph import support_graph

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Customer Support Resolution Agent API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tools_router)
app.include_router(voice_router)

PENDING_APPROVALS = {}
AUDIT_LOGS = []
LANGGRAPH_TRACES: List[Dict[str, Any]] = []


class LoginRequest(BaseModel):
    email: str
    password: str


class ChatTicketRequest(BaseModel):
    text: str


class ApprovalDecisionRequest(BaseModel):
    ticket_id: str
    decision: str  # "approved" or "rejected"


@app.get("/")
def read_root():
    return {"message": "Running"}


@app.post("/auth/login")
def login(payload: LoginRequest):
    email_clean = payload.email.lower().strip()
    user_record = USER_CREDENTIALS.get(email_clean)

    if not user_record or not verify_password(
        payload.password, user_record["password_hash"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(
        user_id=user_record["user_id"],
        email=email_clean,
        role=user_record["role"],
        name=user_record["name"],
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_record["user_id"],
            "name": user_record["name"],
            "email": email_clean,
            "role": user_record["role"],
        },
    }


@app.get("/customer/account")
def get_customer_account(
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    customer = db.query(CustomerModel).filter(CustomerModel.id == auth.user_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer account not found")

    orders = (
        db.query(OrderModel)
        .filter(OrderModel.customer_id == auth.user_id)
        .all()
    )
    shipments = {s.order_id: s for s in db.query(ShipmentModel).all()}

    total_spent = sum(o.total for o in orders)
    total_refunded = sum(o.total for o in orders if o.status == "Refunded")
    pending_refunds = sum(
        item["amount"]
        for item in PENDING_APPROVALS.values()
        if item["customer_id"] == auth.user_id
    )

    return {
        "profile": {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "tier": customer.tier,
        },
        "payment_summary": {
            "total_billed": round(total_spent, 2),
            "total_refunded": round(total_refunded, 2),
            "pending_refund_amount": round(pending_refunds, 2),
            "net_charged": round(total_spent - total_refunded, 2),
            "payment_method": "Visa •••• 4242",
        },
        "orders": [
            {
                "id": o.id,
                "items": o.items,
                "total": o.total,
                "status": o.status,
                "placed_at": o.placed_at.strftime("%b %d, %Y") if o.placed_at else "N/A",
                "carrier": shipments[o.id].carrier if o.id in shipments else "N/A",
                "shipment_status": shipments[o.id].status if o.id in shipments else "N/A",
            }
            for o in orders
        ],
    }


@app.get("/db/overview")
def get_db_overview(
    admin: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
):
    customers = db.query(CustomerModel).all()
    orders = db.query(OrderModel).all()
    shipments = {s.order_id: s for s in db.query(ShipmentModel).all()}

    return {
        "customers": [
            {"id": c.id, "name": c.name, "email": c.email, "tier": c.tier}
            for c in customers
        ],
        "orders": [
            {
                "id": o.id,
                "customer_id": o.customer_id,
                "items": o.items,
                "total": o.total,
                "status": o.status,
                "carrier": shipments[o.id].carrier if o.id in shipments else "N/A",
                "shipment_status": shipments[o.id].status if o.id in shipments else "N/A",
            }
            for o in orders
        ],
        "audit_logs": AUDIT_LOGS[-25:],
    }


# ─── LangGraph Traces Endpoint ─────────────────────────────────────
@app.get("/traces")
def get_langgraph_traces(admin: AuthContext = Depends(require_admin)):
    """Return the last 50 LangGraph execution traces with per-node timing."""
    return LANGGRAPH_TRACES[-50:]


def _collect_node_traces(initial_state: dict, config: dict) -> tuple:
    """
    Run the LangGraph support_graph step-by-step, collecting per-node
    timing data. Returns (final_result, list_of_node_traces).
    """
    node_traces = []
    graph_start = time.time()

    # Use stream to get per-node events from the graph
    final_result = {}
    for event in support_graph.stream(initial_state, config=config):
        # Each event is a dict: { "node_name": { ...output_state... } }
        for node_name, node_output in event.items():
            node_start = time.time()
            # The node has already executed by the time we receive the event,
            # so we record output metadata
            node_end = time.time()

            output_keys = list(node_output.keys()) if isinstance(node_output, dict) else []

            node_traces.append({
                "node": node_name,
                "start_time": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
                "end_time": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
                "duration_ms": round((node_end - node_start) * 1000, 1),
                "input_keys": list(initial_state.keys()) if not node_traces else list(final_result.keys()),
                "output_keys": output_keys,
            })

            # Merge node output into the running state
            if isinstance(node_output, dict):
                final_result.update(node_output)

    graph_end = time.time()
    total_ms = round((graph_end - graph_start) * 1000, 1)

    return final_result, node_traces, total_ms


@app.post("/chat/support")
def handle_chat_ticket(
    payload: ChatTicketRequest,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    text = payload.text
    customer_orders = (
        db.query(OrderModel)
        .filter(OrderModel.customer_id == auth.user_id)
        .all()
    )

    order_match = re.search(r"\bord_\d+\b", text.lower())
    if order_match:
        requested_order_id = order_match.group(0)
        order_record = (
            db.query(OrderModel).filter(OrderModel.id == requested_order_id).first()
        )
        if auth.role == "customer" and (
            not order_record or order_record.customer_id != auth.user_id
        ):
            return {
                "ticket_id": f"sec_{uuid.uuid4().hex[:6]}",
                "final_reply": (
                    f"Access Denied: Order '{requested_order_id}' was not found under your account. "
                    "For your security, you can only view or modify orders linked to your profile."
                ),
                "approval_status": None,
                "is_escalated": False,
            }
        order_id = requested_order_id
    else:
        order_record = customer_orders[0] if customer_orders else None
        order_id = order_record.id if order_record else "ord_101"

    amount = float(order_record.total) if order_record else 50.0
    ticket_id = f"tkt_{uuid.uuid4().hex[:8]}"

    initial_state = {
        "ticket_id": ticket_id,
        "customer_id": auth.user_id,
        "ticket_text": text,
        "intent": None,
        "urgency": None,
        "sentiment": None,
        "extracted_entities": {
            "order_id": order_id,
            "amount": amount,
        },
        "triage_confidence": 1.0,
        "policy_citation": None,
        "policy_decision": None,
        "policy_reasoning": None,
        "planned_actions": [],
        "execution_results": [],
        "requires_approval": False,
        "approval_status": None,
        "is_escalated": False,
        "escalation_summary": None,
        "final_reply": None,
        "messages": [],
    }

    config = {"configurable": {"thread_id": ticket_id}}

    # Run graph with node-level tracing
    result, node_traces, total_ms = _collect_node_traces(initial_state, config)

    # Store the LangGraph trace
    LANGGRAPH_TRACES.append({
        "ticket_id": ticket_id,
        "timestamp": datetime.utcnow().strftime("%H:%M:%S UTC"),
        "customer_id": auth.user_id,
        "ticket_text": text,
        "total_duration_ms": total_ms,
        "node_traces": node_traces,
    })

    if result.get("approval_status") == "pending":
        PENDING_APPROVALS[ticket_id] = {
            "ticket_id": ticket_id,
            "customer_id": auth.user_id,
            "ticket_text": text,
            "order_id": order_id,
            "amount": amount,
            "intent": result.get("intent"),
            "policy_citation": result.get("policy_citation"),
            "status": "pending",
        }

    AUDIT_LOGS.append(
        {
            "ticket_id": ticket_id,
            "timestamp": datetime.utcnow().strftime("%H:%M:%S UTC"),
            "customer_id": auth.user_id,
            "order_id": order_id,
            "amount": amount,
            "text": text,
            "intent": result.get("intent"),
            "policy_decision": result.get("policy_decision"),
            "policy_citation": result.get("policy_citation"),
            "approval_status": result.get("approval_status"),
            "is_escalated": result.get("is_escalated"),
            "escalation_summary": result.get("escalation_summary"),
        }
    )

    return {
        "ticket_id": ticket_id,
        "final_reply": result.get("final_reply"),
        "approval_status": result.get("approval_status"),
        "is_escalated": result.get("is_escalated"),
    }


@app.get("/approvals/pending")
def list_pending_approvals(admin: AuthContext = Depends(require_admin)):
    return list(PENDING_APPROVALS.values())


@app.post("/approvals/decide")
def decide_approval(
    payload: ApprovalDecisionRequest,
    admin: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
):
    item = PENDING_APPROVALS.get(payload.ticket_id)
    if not item:
        raise HTTPException(status_code=404, detail="Pending approval ticket not found")

    if payload.decision == "approved":
        order = db.query(OrderModel).filter(OrderModel.id == item["order_id"]).first()
        if order:
            order.status = "Refunded"
            db.commit()
        item["status"] = "approved"
        reply = f"Approved by {admin.user_id}: Refund of ${item['amount']:,.2f} issued for {item['order_id']}."
    else:
        item["status"] = "rejected"
        reply = f"Rejected by {admin.user_id}: High-value refund request escalated to specialist team."

    del PENDING_APPROVALS[payload.ticket_id]
    return {"ticket_id": payload.ticket_id, "status": item["status"], "reply": reply}

@app.post("/orders/{order_id}/confirm-pickup")
def confirm_carrier_pickup(
    order_id: str,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order or (auth.role == "customer" and order.customer_id != auth.user_id):
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "Return Initiated":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot confirm pickup when order status is '{order.status}'. Initiate a return first.",
        )

    order.status = "Return Picked Up"
    shipment = db.query(ShipmentModel).filter(ShipmentModel.order_id == order_id).first()
    if shipment:
        shipment.status = "Picked Up by Courier - In transit to warehouse"
    db.commit()
    return {"order_id": order.id, "status": order.status}
