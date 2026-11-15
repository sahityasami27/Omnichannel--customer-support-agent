from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_voice_order_status():
    files = {"audio": ("test.wav", b"dummy_audio_bytes", "audio/wav")}
    data = {
        "customer_id": "cust_001",
        "fallback_transcript": "Where is my order ord_101?"
    }
    response = client.post("/voice/support", files=files, data=data)
    assert response.status_code == 200
    res = response.json()
    assert res["intent"] == "order_status"
    assert res["requires_approval"] is False
    assert res["approval_status"] == "approved"

def test_voice_high_value_refund_triggers_approval_gate():
    files = {"audio": ("test.wav", b"dummy_audio_bytes", "audio/wav")}
    data = {
        "customer_id": "cust_002",
        "fallback_transcript": "Issue a refund of 3500 for order ord_102."
    }
    response = client.post("/voice/support", files=files, data=data)
    assert response.status_code == 200
    res = response.json()
    assert res["intent"] == "refund_request"
    assert res["requires_approval"] is True
    assert res["approval_status"] == "pending"
    assert "paused execution" in res["spoken_reply"]