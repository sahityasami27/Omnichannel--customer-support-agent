Omnichannel AI Customer Support Resolution Agent

A production-grade, secure, multi-tenant AI Customer Support Resolution Agent. The system features a unified text/voice omnichannel interface, role-based access control (RBAC), deterministic guardrails for high-value operations, and database-backed order lifecycle management.

🚀 Features

Deterministic LangGraph State Machine: Orchestrates a 3-node workflow (Triage → Policy → Resolution) to handle complex e-commerce lifecycles with 100% evaluation suite pass rates.

Zero-Trust RBAC & Tenant Isolation: Implements HMAC-SHA256 JWT authentication and salted PBKDF2 passwords, eliminating Insecure Direct Object Reference (IDOR) vulnerabilities across dual Customer and Admin portals.

Database-Aware LLM Guardrails: Integrates with live SQLite state to automate 100% of "Return-First" logistical validations (e.g., blocking refunds for items still in transit).

Manager Approval Gate: Automatically intercepts and routes high-value automated refunds (>$2,000) to a secure admin queue for manual sign-off.

Omnichannel Voice Processing: Achieves sub-400ms reasoning times per ticket while seamlessly processing omnichannel inputs via Groq Whisper (Speech-to-Text) and edge-tts (Text-to-Speech).

Real-Time Admin Console: A Next.js operational dashboard featuring live SQLite telemetry, dynamic pending-approval queues, and granular node-by-node LangGraph execution audit traces.

🛠️ Technology Stack

Backend: FastAPI (Python), LangGraph, SQLAlchemy, SQLite

Frontend: Next.js (TypeScript, Tailwind CSS)

Voice Integration: Groq Whisper (whisper-large-v3-turbo), edge-tts

Security: JWT-based Authentication, PBKDF2 Password Hashing

📦 Installation & Setup

1. Clone the Repository

git clone https://github.com/sahityasami27/customer-support-agent.git
cd customer-support-agent


2. Backend Setup (FastAPI)

Open a terminal in the root directory:

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies (ensure you have your requirements.txt set up)
pip install -r requirements.txt

# Seed the initial SQLite database with mock customers, orders, and shipments
python reset.py

# Start the FastAPI server
python -m uvicorn backend.app.main:app --reload --port 8000


3. Frontend Setup (Next.js)

Open a second terminal and navigate to the frontend directory:

cd frontend
npm install
npm run dev


🔐 Test Accounts

Once both servers are running, open http://localhost:3000 in your browser. Use the following credentials to test the RBAC and tenant isolation:

Admin / Operations Manager:

Portal: Redirects automatically to /admin

Email: admin@support.io

Password: adminpassword

Customer (Gold Tier):

Portal: Customer Storefront (restricted to own orders)

Email: elena.r@designstudio.co

Password: password123

Customer (Standard Tier):

Email: alice.j@verizon.net

Password: password123

🧠 Core Business Logic Flow

Pre-Delivery: Refunds and returns are blocked for items marked as Processing, Shipped, or Delayed.

Delivered: Direct refunds are blocked. Customers must initiate a formal return to transition the item into a Return Initiated state and schedule carrier pickup.

Return Picked Up: Financial refunds are unlocked only after confirmation that the physical item has been scanned by the logistics courier.

Approval Gate: If the refund exceeds $2,000, the LangGraph workflow pauses and routes the ticket to the Admin Console for manual approval.
