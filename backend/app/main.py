import os
import datetime
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from dotenv import load_dotenv

from .database import engine, get_db, Base, SessionLocal
from .models import (
    User, HCPProfile, Interaction, InteractionProduct, InteractionMaterial,
    InteractionEdit, FollowUpTask, ChatMessage, ToolExecutionLog, AuditLog
)
from .schemas import (
    ChatMessageOut, InteractionOut, InteractionCreate, InteractionUpdate,
    ValidationReport, NextBestActionRequest, NextBestActionResponse,
    ToolExecutionLogOut, AuditLogOut, ChatRequest, ChatResponse
)
from .agent import agent_workflow, crm_validation_tool, next_best_action_tool, groq_client
from .websockets import manager

load_dotenv()

app = FastAPI(
    title="AI-First CRM - HCP Interaction Management Backend",
    description="Enterprise Pharma CRM Backend driven by LangGraph Agent",
    version="1.0.0"
)

# CORS middleware configuration for React frontend local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup DB Tables Creation & Seeding
@app.on_event("startup")
def startup_db_setup():
    # Auto-create tables
    Base.metadata.create_all(bind=engine)
    print("Database tables validated/created.")

    # Seed initial data if database is empty
    db = SessionLocal()
    try:
        # Check if users table is empty
        if db.query(User).count() == 0:
            print("Seeding initial users...")
            user1 = User(username="rep_muthu", email="muthu@pharmaco.com", role="Medical Representative")
            user2 = User(username="manager_alex", email="alex@pharmaco.com", role="Regional Manager")
            db.add_all([user1, user2])
            db.commit()

        # Check if HCP profiles table is empty
        if db.query(HCPProfile).count() == 0:
            print("Seeding initial HCP Profiles...")
            hcp1 = HCPProfile(name="Dr. Sarah Johnson", specialty="Cardiologist", hospital_clinic="Apollo Hospital", tier="A", territory="Metro North")
            hcp2 = HCPProfile(name="Dr. John Doe", specialty="Neurologist", hospital_clinic="City Medical Center", tier="B", territory="Metro West")
            hcp3 = HCPProfile(name="Dr. Lisa Ray", specialty="Orthopedic Specialist", hospital_clinic="Grace Clinic", tier="C", territory="South Zone")
            db.add_all([hcp1, hcp2, hcp3])
            db.commit()

            # Seed pre-existing interactions to show historical data
            print("Seeding previous interactions...")
            # Interaction with Dr. Sarah Johnson
            intr = Interaction(
                hcp_id=hcp1.id,
                hcp_name=hcp1.name,
                specialty=hcp1.specialty,
                hospital_clinic=hcp1.hospital_clinic,
                tier=hcp1.tier,
                territory=hcp1.territory,
                interaction_date=datetime.date.today() - datetime.timedelta(days=15),
                interaction_type="In-Person",
                visit_objective="Product Detailing",
                key_discussion_points="Reviewed CardioMax clinical outcomes. Doctor expressed interest in efficacy data.",
                objections_raised="Expressed minor concern about dosage options for geriatric patients.",
                sentiment="Positive",
                outcome="Requested clinical trial papers.",
                follow_up_required=True,
                follow_up_date=datetime.date.today() - datetime.timedelta(days=7),
                next_best_action="Email clinical trials and efficacy study.",
                interaction_summary="Dr. Sarah showed high interest in CardioMax. We addressed age-related safety concerns.",
                validation_status="Valid"
            )
            db.add(intr)
            db.flush()
            db.add(InteractionProduct(interaction_id=intr.id, product_name="CardioMax"))
            db.add(InteractionMaterial(interaction_id=intr.id, material_name="CardioMax Brochure"))
            db.add(AuditLog(action="SEED_INTERACTION", table_name="interactions", record_id=intr.id, details="Seeded previous interaction with Dr. Sarah Johnson"))
            db.commit()
            print("Database seeding completed.")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

# WebSocket Endpoint for streaming real-time notifications
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We listen for any incoming heartbeats or commands
            data = await websocket.receive_text()
            print(f"Received from WebSocket client: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# API - Chat endpoint (Main AI-driven interaction entry)
@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_agent(payload: ChatRequest, db: Session = Depends(get_db)):
    try:
        user_message = payload.message
        
        # Save user message to database
        db_user_msg = ChatMessage(sender="user", message=user_message, timestamp=datetime.datetime.utcnow())
        db.add(db_user_msg)
        db.commit()

        # Fetch chat history for context (last 10 messages)
        db_history = db.query(ChatMessage).order_by(ChatMessage.timestamp.desc()).limit(10).all()
        history = [{"sender": msg.sender, "message": msg.message} for msg in reversed(db_history)]

        # Fetch active/last interaction to act as current form state
        db_intr = db.query(Interaction).filter(Interaction.is_deleted == False).order_by(Interaction.updated_at.desc()).first()
        
        interaction_dict = {}
        if db_intr:
            interaction_dict = {
                "id": db_intr.id,
                "hcp_name": db_intr.hcp_name,
                "specialty": db_intr.specialty,
                "hospital_clinic": db_intr.hospital_clinic,
                "tier": db_intr.tier,
                "territory": db_intr.territory,
                "interaction_date": db_intr.interaction_date.isoformat(),
                "interaction_type": db_intr.interaction_type,
                "visit_objective": db_intr.visit_objective,
                "key_discussion_points": db_intr.key_discussion_points,
                "objections_raised": db_intr.objections_raised,
                "sentiment": db_intr.sentiment,
                "outcome": db_intr.outcome,
                "follow_up_required": db_intr.follow_up_required,
                "follow_up_date": db_intr.follow_up_date.isoformat() if db_intr.follow_up_date else None,
                "next_best_action": db_intr.next_best_action,
                "interaction_summary": db_intr.interaction_summary,
                "validation_status": db_intr.validation_status,
                "products_discussed": [p.product_name for p in db_intr.products],
                "materials_shared": [m.material_name for m in db_intr.materials]
            }

        # Initialize LangGraph state input
        state_input = {
            "messages": history,
            "interaction_data": interaction_dict,
            "current_tool": "",
            "validation_status": interaction_dict.get("validation_status", "Pending"),
            "conversation_memory": [],
            "audit_log": [],
            "tool_logs": []
        }

        # Run LangGraph StateGraph Workflow
        result_state = agent_workflow.invoke(
            state_input,
            config={"configurable": {"db": db}}
        )

        # Extract generated response message
        assistant_resp_text = "I have processed your request."
        if result_state["messages"]:
            last_msg = result_state["messages"][-1]
            if last_msg["sender"] == "assistant":
                assistant_resp_text = last_msg["message"]

        # Save assistant message to database
        db_assistant_msg = ChatMessage(sender="assistant", message=assistant_resp_text, timestamp=datetime.datetime.utcnow())
        db.add(db_assistant_msg)
        db.commit()

        # Retrieve updated/active interaction details to return to frontend
        active_data = result_state.get("interaction_data", {})
        
        # Format tool execution logs for delivery
        logs_delivered = result_state.get("tool_logs", [])

        # Broadcast the state change over WebSocket
        await manager.broadcast({
            "type": "CRM_STATE_UPDATE",
            "interaction_data": active_data,
            "tool_logs": logs_delivered,
            "validation_status": result_state.get("validation_status", "Pending"),
            "latest_message": {
                "sender": "assistant",
                "message": assistant_resp_text,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        })

        return ChatResponse(
            response=assistant_resp_text,
            interaction_data=active_data,
            current_tool=result_state.get("current_tool"),
            validation_status=result_state.get("validation_status"),
            tool_execution_logs=logs_delivered
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent process exception: {str(e)}")

# API - Interactions CRUD
@app.post("/api/interactions", response_model=InteractionOut)
def create_interaction(payload: InteractionCreate, db: Session = Depends(get_db)):
    # Standard manual logging backend fallback endpoint
    hcp_name = payload.hcp_name
    db_hcp = db.query(HCPProfile).filter(HCPProfile.name == hcp_name).first()
    if not db_hcp:
        db_hcp = HCPProfile(name=hcp_name, specialty=payload.specialty, hospital_clinic=payload.hospital_clinic, tier=payload.tier, territory=payload.territory)
        db.add(db_hcp)
        db.flush()

    intr = Interaction(
        hcp_id=db_hcp.id,
        hcp_name=hcp_name,
        specialty=payload.specialty,
        hospital_clinic=payload.hospital_clinic,
        tier=payload.tier,
        territory=payload.territory,
        interaction_date=payload.interaction_date,
        interaction_type=payload.interaction_type,
        visit_objective=payload.visit_objective,
        key_discussion_points=payload.key_discussion_points,
        objections_raised=payload.objections_raised,
        sentiment=payload.sentiment,
        outcome=payload.outcome,
        follow_up_required=payload.follow_up_required,
        follow_up_date=payload.follow_up_date,
        next_best_action=payload.next_best_action,
        interaction_summary=payload.interaction_summary,
        validation_status=payload.validation_status
    )
    db.add(intr)
    db.flush()

    for p in payload.products:
        db.add(InteractionProduct(interaction_id=intr.id, product_name=p))
    for m in payload.materials:
        db.add(InteractionMaterial(interaction_id=intr.id, material_name=m))

    db.add(AuditLog(action="CREATE_INTERACTION", table_name="interactions", record_id=intr.id, details="Created interaction manually"))
    db.commit()
    return intr

@app.put("/api/interactions/{id}", response_model=InteractionOut)
def update_interaction(id: int, payload: InteractionUpdate, db: Session = Depends(get_db)):
    intr = db.query(Interaction).filter(Interaction.id == id, Interaction.is_deleted == False).first()
    if not intr:
        raise HTTPException(status_code=404, detail="Interaction not found")

    # Track fields changed for audit
    update_data = payload.dict(exclude_unset=True)
    for field, new_val in update_data.items():
        if field in ["products", "materials"]:
            continue
        old_val = getattr(intr, field)
        if old_val != new_val:
            db.add(InteractionEdit(
                interaction_id=intr.id,
                field_name=field,
                old_value=str(old_val) if old_val is not None else "",
                new_value=str(new_val) if new_val is not None else ""
            ))
            setattr(intr, field, new_val)

    if payload.products is not None:
        db.query(InteractionProduct).filter(InteractionProduct.interaction_id == id).delete()
        for p in payload.products:
            db.add(InteractionProduct(interaction_id=id, product_name=p))

    if payload.materials is not None:
        db.query(InteractionMaterial).filter(InteractionMaterial.interaction_id == id).delete()
        for m in payload.materials:
            db.add(InteractionMaterial(interaction_id=id, material_name=m))

    intr.updated_at = datetime.datetime.utcnow()
    db.add(AuditLog(action="UPDATE_INTERACTION", table_name="interactions", record_id=id, details="Updated interaction properties"))
    db.commit()
    db.refresh(intr)
    return intr

@app.get("/api/interactions/{id}", response_model=InteractionOut)
def get_interaction(id: int, db: Session = Depends(get_db)):
    intr = db.query(Interaction).filter(Interaction.id == id, Interaction.is_deleted == False).first()
    if not intr:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return intr

@app.get("/api/interactions", response_model=List[InteractionOut])
def list_interactions(db: Session = Depends(get_db)):
    return db.query(Interaction).filter(Interaction.is_deleted == False).order_by(Interaction.updated_at.desc()).all()

# API - HCP Historical Context History
@app.get("/api/hcp/{id}/history", response_model=List[InteractionOut])
def get_hcp_history(id: int, db: Session = Depends(get_db)):
    hcp = db.query(HCPProfile).filter(HCPProfile.id == id, HCPProfile.is_deleted == False).first()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")
    return db.query(Interaction).filter(Interaction.hcp_id == hcp.id, Interaction.is_deleted == False).order_by(Interaction.interaction_date.desc()).all()

# API - Validate CRM interaction data
@app.post("/api/validate", response_model=ValidationReport)
def validate_crm_data(payload: dict):
    report = crm_validation_tool(payload)
    return report

# API - Recommended Next Best Actions
@app.post("/api/next-best-action", response_model=NextBestActionResponse)
def get_next_best_action_api(payload: NextBestActionRequest):
    data = {
        "products_discussed": payload.products,
        "sentiment": payload.sentiment,
        "objections_raised": payload.objections
    }
    result = next_best_action_tool(data)
    return NextBestActionResponse(
        next_best_action=result["next_best_action"],
        recommended_materials=result["recommended_materials"],
        suggested_topics=result["suggested_topics"]
    )

# API - Chat history list
@app.get("/api/chat/history", response_model=List[ChatMessageOut])
def get_chat_history(db: Session = Depends(get_db)):
    return db.query(ChatMessage).order_by(ChatMessage.timestamp.asc()).all()

# API - Tool Execution Logs
@app.get("/api/tool-logs", response_model=List[ToolExecutionLogOut])
def get_tool_logs(db: Session = Depends(get_db)):
    return db.query(ToolExecutionLog).order_by(ToolExecutionLog.executed_at.desc()).all()

# API - Audit Trail Logs
@app.get("/api/audit-logs", response_model=List[AuditLogOut])
def get_audit_logs(db: Session = Depends(get_db)):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()

@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        import tempfile
        import os
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name
        try:
            if groq_client.client:
                with open(temp_path, "rb") as audio_file:
                    transcription = groq_client.client.audio.transcriptions.create(
                        file=(file.filename or "audio.wav", audio_file),
                        model="whisper-large-v3",
                        temperature=0.0
                    )
                text = transcription.text
            else:
                text = "Met Dr. John Doe at Apollo Hospital. Discussed CardioMax and LipidBloc efficacy. Sentiment was positive. Left some brochures."
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        return {"text": text}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
