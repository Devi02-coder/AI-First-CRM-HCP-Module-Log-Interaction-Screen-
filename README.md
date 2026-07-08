<<<<<<< HEAD
# AI-First CRM - HCP Interaction Management Screen

An enterprise pharma CRM module powered by a LangGraph agent that enables medical representatives to log and manage interactions with Healthcare Professionals (HCPs) using natural language, voice notes, and real-time form sync.

---

## Features

1. **Natural Language Logging**: Input details about meetings, calls, remote sessions, and have the system parse fields (HCP name, products discussed, sentiment, materials shared, follow-up, etc.) automatically.
2. **Form Autofill & Validation**: Real-time validation checks for CRM compliance guidelines (e.g., matching follow-up dates and ensuring mandatory fields).
3. **Voice Note (Speech-to-Text)**:
   - **Textarea Transcription**: Click the mic icon next to the "Topics Discussed" area to record and transcribe key discussion points.
   - **Voice Note Summarization**: Record a voice note, request user consent, and automatically submit it to the AI Assistant to parse and populate the CRM form.
4. **Edit Interaction Tool**: Issue conversational corrections like *"Sorry, the name was actually Dr. John and the sentiment was negative"* to update specific fields on the form automatically.
5. **Timeline & Audit Logs**: Detailed audit history tracking updates to the interaction forms.

---

## Project Structure

```text
├── backend/            # FastAPI & LangGraph backend
│   ├── app/            # Application logic, agents, DB models, and API routes
│   └── requirements.txt# Python dependencies
└── frontend/           # React + TypeScript + Redux + Vite frontend
    ├── src/            # Source components (ChatPanel, InteractionForm, store)
    └── package.json    # Frontend dependencies and run scripts
```

---

## Getting Started

### Prerequisites
- **Python**: v3.10+
- **Node.js**: v18+
- **MySQL**: Running local instance

---

### Backend Configuration & Running

1. **Setup Env**:
   Inside `backend/`, copy/update the `.env` file with your MySQL database details and your Groq API Key:
   ```ini
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=YOUR_PASSWORD
   DB_NAME=hcp_crm
   GROQ_API_KEY=YOUR_GROQ_API_KEY
   ```
2. **Install Dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
3. **Run Backend Server**:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

---

### Frontend Configuration & Running

1. **Install Frontend Dependencies**:
   ```bash
   cd frontend
   npm install
   ```
2. **Run Dev Server**:
   ```bash
   npm run dev
   ```
   Open [http://localhost:5173/](http://localhost:5173/) to access the interface.
=======
# AI-First-CRM-HCP-Module-Log-Interaction-Screen-
AI-powered HCP CRM platform built with React, FastAPI, LangGraph, Groq LLM, and MySQL. Log, edit, and manage healthcare professional interactions using natural language and voice commands with automatic AI-driven form population and CRM workflow automation.
>>>>>>> 9c0aa4c2071044ef90b2a1302ae661f05cbc201c
