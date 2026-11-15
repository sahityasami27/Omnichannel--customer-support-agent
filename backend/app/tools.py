from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import json  

from .database import get_db
from .models import OrderModel, CustomerModel, ShipmentModel, TicketModel, ActionModel
from .schemas import (
    OrderLookupRequest, CustomerLookupRequest, ShipmentStatusRequest, CreateRefundRequest, CreateReshipmentRequest, UpdateAddressRequest, AddTicketNoteRequest, EscalateTicketRequest  
)

router = APIRouter(prefix="/tools", tags=["Mock Store Tools"])

@router.post("/get_order")
def get_order(payload: OrderLookupRequest, db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "order_id":order.id,
        "customer_id": order.customer_id,
        "items": order.items,
        "total": order.total,
        "status": order.status,
        "placed_at": order.placed_at.isoformat(),
        "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None
    }

@router.post("/get_customer")
def get_customer(payload: CustomerLookupRequest, db: Session = Depends(get_db)):
    customer = db.query(CustomerModel).filter(CustomerModel.id == payload.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return{
        "customer_id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "tier": customer.tier 
    }

@router.post("/get_shipment_status")
def get_shipment_status(payload: ShipmentStatusRequest, db: Session = Depends(get_db)):
    shipment = db.query(ShipmentModel).filter(ShipmentModel.id == payload.shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return{
        "shipment_id": shipment.id,
        "order_id": shipment.order_id,
        "carrier": shipment.carrier,
        "status": shipment.status,
        "last_update": shipment.last_update.isoformat()
    }

@router.post("/create_refund")
def create_refund(payload: CreateRefundRequest, db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = "Refunded"
    db.commit()
    return{
        "status": "success",
        "message": f"Successfully issued refund of {payload.amount} for order {payload.order_id}.",
        "reason": payload.reason
    }
    
@router.post("/create_reshipment")
def create_reshipment(payload: CreateReshipmentRequest, db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "status": "success",
        "message": f"Successfully created a reshipment order for original order {payload.order_id}.",
    }