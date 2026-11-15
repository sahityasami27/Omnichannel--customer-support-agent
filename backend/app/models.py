from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from .database import Base

class CustomerModel(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    tier = Column(String, default="Standard")

    orders = relationship("OrderModel", back_populates="customer")
    tickets = relationship("TicketModel", back_populates="customer")

class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    items = Column(Text, nullable=False)
    total = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    placed_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)

    customer = relationship("CustomerModel", back_populates="orders")
    shipments = relationship("ShipmentModel", back_populates="order")

class ShipmentModel(Base):
    __tablename__ = "shipments"

    id = Column(String, primary_key=True, index=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    carrier = Column(String, nullable=False)
    status = Column(String, nullable=False)
    last_update = Column(DateTime, default=datetime.utcnow)

    order = relationship("OrderModel", back_populates="shipments")

class TicketModel(Base):
    __tablename__ = "tickets"

    id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    text = Column(Text, nullable=False)
    intent = Column(String, nullable=True)
    status = Column(String, default="Open")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    customer = relationship("CustomerModel", back_populates="tickets")
    actions = relationship("ActionModel", back_populates="ticket")

class ActionModel(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String, ForeignKey("tickets.id"), nullable=False)
    tool = Column(String, nullable=False)
    args = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("TicketModel", back_populates="actions")

class PolicyModel(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    content = Column(Text, nullable=False)