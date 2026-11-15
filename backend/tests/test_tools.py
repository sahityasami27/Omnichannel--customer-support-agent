from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Customer Support Resolution Agent Backend is running."}

def test_get_order_success():
    response = client.post("/tools/get_order", json={"order_id": "ord_101"})
    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == "ord_101"
    assert data["customer_id"] == "cust_001"
    assert data["total"] == 45.50

def test_get_order_not_found():
    response = client.post("/tools/get_order", json={"order_id": "ord_999"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"

def test_get_customer_success():
    response = client.post("/tools/get_customer", json={"customer_id": "cust_002"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Bob Smith"
    assert data["tier"] == "VIP"

def test_get_shipment_status():
    response = client.post("/tools/get_shipment_status", json={"shipment_id": "shp_501"})
    assert response.status_code == 200
    data = response.json()
    assert data["carrier"] == "FedEx"
    assert data["status"] == "Delivered"

def test_create_refund():
    response = client.post("/tools/create_refund", json={
        "order_id": "ord_101",
        "amount": 45.50,
        "reason": "Customer requested refund"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Verify order status changed to Refunded
    order_check = client.post("/tools/get_order", json={"order_id": "ord_101"})
    assert order_check.json()["status"] == "Refunded"