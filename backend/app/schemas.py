from pydantic import BaseModel, Field

class OrderLookupRequest(BaseModel):
    order_id: str

class CustomerLookupRequest(BaseModel):
    customer_id: str

class ShipmentStatusRequest(BaseModel):
    shipment_id: str

class CreateRefundRequest(BaseModel):
    order_id: str
    amount: float = Field(..., gt=0, description="Refund amount must be greater than 0")
    reason: str

class CreateReshipmentRequest(BaseModel):
    order_id: str
    reason: str

class UpdateAddressRequest(BaseModel):
    order_id: str
    new_address: str

class AddTicketNoteRequest(BaseModel):
    ticket_id: str
    note: str

class EscalateTicketRequest(BaseModel):
    ticket_id: str
    summary: str