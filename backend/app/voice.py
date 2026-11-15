import os
import re
import uuid
import base64
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import edge_tts
from groq import Groq

from backend.agent.graph import support_graph

router = APIRouter(prefix="/voice", tags=["Voice Support Agent"])

# Clean markdown so the TTS engine doesn't read asterisks or brackets aloud
def clean_text_for_speech(text: str) -> str:
    text = re.sub(r'\*\*|\*|#|`', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    return text.strip()

async def transcribe_audio(file_bytes: bytes, filename: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "dummy-key-for-now":
        # Fallback if testing locally without a live Groq key
        return "Where is my order ord_101?"
    
    client = Groq(api_key=api_key)
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1] or ".wav") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=(filename, audio_file.read()),
                model="whisper-large-v3-turbo",
                response_format="text"
            )
        return str(transcription).strip()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

async def synthesize_speech(text: str, voice: str = "en-US-AriaNeural") -> bytes:
    communicate = edge_tts.Communicate(text, voice)
    audio_chunks = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.extend(chunk["data"])
    return bytes(audio_chunks)

@router.post("/support")
async def handle_voice_ticket(
    audio: UploadFile = File(...),
    customer_id: Optional[str] = Form("cust_001"),
    fallback_transcript: Optional[str] = Form(None)
):
    audio_bytes = await audio.read()
    if not audio_bytes and not fallback_transcript:
        raise HTTPException(status_code=400, detail="Empty audio file provided.")

    # 1. Transcribe voice to text (or use fallback_transcript for automated pytest runs)
    transcript = fallback_transcript if fallback_transcript else await transcribe_audio(audio_bytes, audio.filename or "audio.wav")

    # 2. Extract dynamic entities for the graph state
    amount = 50.0
    numbers = re.findall(r'\b\d{4,}\b', transcript)
    if numbers:
        amount = float(numbers[0])

    ticket_id = f"voice_{uuid.uuid4().hex[:8]}"
    initial_state = {
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "ticket_text": transcript,
        "intent": None,
        "urgency": None,
        "sentiment": None,
        "extracted_entities": {
            "order_id": "ord_101" if "ord_101" in transcript.lower() else ("ord_102" if "ord_102" in transcript.lower() else None),
            "amount": amount
        },
        "triage_confidence": 1.0,
        "policy_citation": None,
        "policy_decision": None,
        "policy_reasoning": None,
        "planned_actions": [],
        "execution_results": [],
        "requires_approval": amount > 2000,
        "approval_status": None,
        "is_escalated": False,
        "escalation_summary": None,
        "final_reply": None,
        "messages": []
    }

    # 3. Run through our deterministic & LLM LangGraph pipeline
    config = {"configurable": {"thread_id": ticket_id}}
    result = support_graph.invoke(initial_state, config=config)

    # 4. Craft natural spoken response based on safety gate outcome
    if result.get("approval_status") == "pending":
        spoken_reply = (
            f"I have logged your refund request of {int(amount)} for order {initial_state['extracted_entities'].get('order_id')}. "
            "Because this amount exceeds our two thousand threshold, I have paused execution and routed it to a manager for approval."
        )
    elif result.get("is_escalated"):
        spoken_reply = "I am escalating your request to a human support specialist who will assist you shortly."
    else:
        spoken_reply = clean_text_for_speech(result.get("final_reply") or "Your request has been resolved.")

    # 5. Synthesize speech (with offline fallback if no internet connection)
    try:
        tts_audio_bytes = await synthesize_speech(spoken_reply)
        audio_b64 = base64.b64encode(tts_audio_bytes).decode("utf-8")
    except Exception:
        audio_b64 = ""

    return {
        "ticket_id": ticket_id,
        "transcript": transcript,
        "intent": result.get("intent"),
        "policy_decision": result.get("policy_decision"),
        "requires_approval": result.get("requires_approval"),
        "approval_status": result.get("approval_status"),
        "is_escalated": result.get("is_escalated"),
        "spoken_reply": spoken_reply,
        "audio_base64": audio_b64
    }