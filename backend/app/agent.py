from typing import List, Dict, Any, TypedDict, Annotated
import datetime
import re
from sqlalchemy.orm import Session
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from .groq_client import GroqClient
from .models import (
    Interaction, InteractionProduct, InteractionMaterial, 
    InteractionEdit, HCPProfile, ToolExecutionLog, AuditLog, ChatMessage
)

# Instantiate the Groq client
groq_client = GroqClient()

# Define the LangGraph State
class CRMState(TypedDict):
    messages: List[Dict[str, Any]]
    interaction_data: Dict[str, Any]
    current_tool: str
    validation_status: str
    conversation_memory: List[Dict[str, Any]]
    audit_log: List[Dict[str, Any]]
    tool_logs: List[Dict[str, Any]]

# --- TOOLS IMPLEMENTATION ---

def log_interaction_tool(text: str) -> Dict[str, Any]:
    """Logs a new interaction by extracting entities."""
    return groq_client.extract_interaction_entities(text)

def edit_interaction_tool(text: str, current_data: Dict[str, Any]) -> Dict[str, Any]:
    """Modifies specific fields of the interaction."""
    updates = groq_client.extract_edit_fields(text, current_data)
    updated_data = {**current_data}
    for k, v in updates.items():
        updated_data[k] = v
    return {
        "updated_data": updated_data,
        "applied_changes": updates
    }

def hcp_context_retrieval_tool(hcp_name: str, db: Session) -> List[Dict[str, Any]]:
    """Retrieves previous interaction logs for a given HCP."""
    # Find HCP profiles matching name
    db_hcp = db.query(HCPProfile).filter(
        HCPProfile.name.like(f"%{hcp_name}%"),
        HCPProfile.is_deleted == False
    ).first()
    
    if not db_hcp:
        return []
    
    interactions = db.query(Interaction).filter(
        Interaction.hcp_id == db_hcp.id,
        Interaction.is_deleted == False
    ).order_by(Interaction.interaction_date.desc()).limit(3).all()
    
    history = []
    for intr in interactions:
        history.append({
            "date": intr.interaction_date.isoformat(),
            "type": intr.interaction_type,
            "objective": intr.visit_objective,
            "sentiment": intr.sentiment,
            "summary": intr.interaction_summary
        })
    return history

def interaction_summary_tool(current_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generates a concise executive medical summary."""
    return groq_client.generate_summary_and_action(current_data)

def next_best_action_tool(current_data: Dict[str, Any]) -> Dict[str, Any]:
    """Suggests next sales intelligence activities."""
    products = current_data.get("products_discussed", ["CardioMax"])
    sentiment = current_data.get("sentiment", "Positive")
    
    if sentiment.lower() == "positive":
        nba = f"Email the therapeutic superiority study on {products[0] if products else 'CardioMax'} to Dr. {current_data.get('hcp_name', 'Johnson')} and coordinate a peer group seminar."
        mats = ["Clinical Trial Efficacy PDF", "KOL Peer Group Discussion Slide Deck"]
        topics = ["Long-term safety data", "Dosage escalation guides"]
    elif sentiment.lower() == "negative":
        nba = f"Schedule an in-person session to address medical safety/objections for {products[0] if products else 'CardioMax'} and invite the Regional Medical Director."
        mats = ["Adverse Event Registry Report", "Clinical Trial Meta-Analysis Study"]
        topics = ["Adverse event management", "Patient screening protocol"]
    else:
        nba = f"Send a follow-up email sharing the standard brochure for {products[0] if products else 'CardioMax'} and confirm the next meeting date."
        mats = ["Standard Product Brochure", "Pricing and Insurance FAQ Guide"]
        topics = ["Standard administration protocol", "Insurance copay program info"]
        
    return {
        "next_best_action": nba,
        "recommended_materials": mats,
        "suggested_topics": topics
    }

def crm_validation_tool(current_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validates CRM interaction data constraints."""
    issues = []
    
    # Check 1: HCP Name is required
    hcp_name = current_data.get("hcp_name")
    if not hcp_name or hcp_name.strip() == "":
        issues.append({"field": "hcp_name", "message": "HCP Name is mandatory.", "severity": "error"})
        
    # Check 2: Interaction Date is required
    date_val = current_data.get("interaction_date")
    if not date_val:
        issues.append({"field": "interaction_date", "message": "Interaction Date is mandatory.", "severity": "error"})
    else:
        try:
            # check format
            if isinstance(date_val, str):
                datetime.date.fromisoformat(date_val)
        except ValueError:
            issues.append({"field": "interaction_date", "message": "Invalid date format. Expected YYYY-MM-DD.", "severity": "error"})

    # Check 3: Products Discussed cannot be empty
    prods = current_data.get("products_discussed")
    if not prods or len(prods) == 0:
        issues.append({"field": "products_discussed", "message": "At least one discussed product must be selected.", "severity": "error"})

    # Check 4: Follow-up Date validation
    follow_up_req = current_data.get("follow_up_required", False)
    follow_up_date = current_data.get("follow_up_date")
    if follow_up_req and not follow_up_date:
        issues.append({"field": "follow_up_date", "message": "Follow-Up Date is mandatory if follow-up is required.", "severity": "error"})
    elif follow_up_req and follow_up_date:
        try:
            f_date = datetime.date.fromisoformat(follow_up_date) if isinstance(follow_up_date, str) else follow_up_date
            i_date = datetime.date.fromisoformat(date_val) if isinstance(date_val, str) else date_val
            if f_date <= i_date:
                issues.append({"field": "follow_up_date", "message": "Follow-Up Date must be after the Interaction Date.", "severity": "error"})
        except Exception:
            pass # already handled by date validation if invalid format

    is_valid = len([i for i in issues if i["severity"] == "error"]) == 0
    status = "Valid" if is_valid else "Invalid"
    
    return {
        "is_valid": is_valid,
        "validation_status": status,
        "issues": issues
    }

# --- LANGGRAPH NODES ---

def user_input_node(state: CRMState) -> Dict[str, Any]:
    """Node 1: Capture user message."""
    messages = state.get("messages", [])
    user_msg = messages[-1] if messages else {"sender": "user", "message": ""}
    return {
        "messages": messages,
        "tool_logs": state.get("tool_logs", []) + [{"step": "User Input Node", "status": "Captured message: " + user_msg.get("message", "")}]
    }

def intent_classification_node(state: CRMState) -> Dict[str, Any]:
    """Node 2: Detect CRM Representative intent."""
    messages = state.get("messages", [])
    user_msg = messages[-1]["message"] if messages else ""
    intent = groq_client.classify_intent(user_msg)
    
    # Map intent to a logical tool execution action
    return {
        "current_tool": intent,
        "tool_logs": state.get("tool_logs", []) + [{"step": "Intent Classification Node", "status": f"Intent identified: {intent.upper()}"}]
    }

def tool_execution_node(state: CRMState, config: RunnableConfig) -> Dict[str, Any]:
    """Node 4: Execute the matching tool logic based on user intent."""
    db: Session = config["configurable"]["db"]
    intent = state.get("current_tool", "simple_chat")
    messages = state.get("messages", [])
    user_msg = messages[-1]["message"] if messages else ""
    current_data = state.get("interaction_data", {})
    
    new_logs = []
    updated_data = {**current_data}
    audit_entries = []
    
    if intent == "log_new":
        new_logs.append({"step": "Tool Execution Node", "status": "Executing Log Interaction Tool"})
        extracted = log_interaction_tool(user_msg)
        updated_data = extracted
        new_logs.append({"step": "Entity Extraction", "status": f"Extracted details for HCP: {extracted.get('hcp_name')}"})
        
        # Auto trigger summary and next action tool inside tool chain
        summary_info = interaction_summary_tool(updated_data)
        updated_data["interaction_summary"] = summary_info.get("interaction_summary")
        updated_data["next_best_action"] = summary_info.get("next_best_action")
        new_logs.append({"step": "Interaction Summary Tool", "status": "Generated CRM executive summary"})
        
        # Auto trigger next best action recommendations
        nba_info = next_best_action_tool(updated_data)
        updated_data["next_best_action"] = nba_info.get("next_best_action")
        new_logs.append({"step": "Next Best Action Tool", "status": "Generated sales intelligence plan"})
        
    elif intent == "edit_existing":
        new_logs.append({"step": "Tool Execution Node", "status": "Executing Edit Interaction Tool"})
        res = edit_interaction_tool(user_msg, current_data)
        updated_data = res["updated_data"]
        changes = res["applied_changes"]
        
        # Track audit entries for edits
        for field, new_val in changes.items():
            old_val = current_data.get(field)
            audit_entries.append({
                "field_name": field,
                "old_value": str(old_val) if old_val is not None else "",
                "new_value": str(new_val) if new_val is not None else "",
            })
            new_logs.append({"step": "Edit Applied", "status": f"Modified field '{field}' to '{new_val}'"})
            
    elif intent == "get_history":
        new_logs.append({"step": "Tool Execution Node", "status": "Executing HCP Context Retrieval Tool"})
        hcp_name = current_data.get("hcp_name", "Sarah Johnson")
        # simple check if user specified a name in query
        hcp_match = re.search(r'dr\.\s+([a-z]+(?:\s+[a-z]+)?)', user_msg, re.IGNORECASE)
        if hcp_match:
            hcp_name = hcp_match.group(1).strip()
            
        history = hcp_context_retrieval_tool(hcp_name, db)
        state["conversation_memory"] = history
        new_logs.append({"step": "HCP History Retrieval", "status": f"Retrieved {len(history)} past interactions for Dr. {hcp_name}"})
        
    elif intent == "validate_form":
        new_logs.append({"step": "Tool Execution Node", "status": "Running CRM Validation Check"})
        # handled by validation node next, but log execution here
        
    elif intent == "get_recommendation":
        new_logs.append({"step": "Tool Execution Node", "status": "Executing Next Best Action Recommendations"})
        nba_info = next_best_action_tool(updated_data)
        updated_data["next_best_action"] = nba_info.get("next_best_action")
        new_logs.append({"step": "Next Best Action Tool", "status": f"Strategic recommendation: {nba_info.get('next_best_action')}"})
        
    return {
        "interaction_data": updated_data,
        "tool_logs": state.get("tool_logs", []) + new_logs,
        "audit_log": state.get("audit_log", []) + audit_entries
    }

def validation_node(state: CRMState) -> Dict[str, Any]:
    """Node 5: Perform validation check on CRM compliance guidelines."""
    current_data = state.get("interaction_data", {})
    intent = state.get("current_tool", "simple_chat")
    
    # We skip validation only if there's no interaction data loaded yet
    if not current_data or intent in ["simple_chat", "get_history"]:
        return {
            "validation_status": "Valid",
            "tool_logs": state.get("tool_logs", []) + [{"step": "Validation Node", "status": "Validation skipped: No active record data"}]
        }
        
    report = crm_validation_tool(current_data)
    status = report["validation_status"]
    
    log_status = f"Compliance Validation: {status.upper()}"
    if not report["is_valid"]:
        log_status += f" (Found {len(report['issues'])} issues)"
        
    return {
        "validation_status": status,
        "tool_logs": state.get("tool_logs", []) + [{"step": "Validation Node", "status": log_status}],
        "interaction_data": {**current_data, "validation_status": status}
    }

def state_update_node(state: CRMState) -> Dict[str, Any]:
    """Node 6: Prepare final state parameters."""
    return {
        "tool_logs": state.get("tool_logs", []) + [{"step": "State Update Node", "status": "State merged and prepared for persistence"}]
    }

def response_generation_node(state: CRMState) -> Dict[str, Any]:
    """Node 7: Generate chatbot conversation response."""
    messages = state.get("messages", [])
    user_msg = messages[-1]["message"] if messages else ""
    current_data = state.get("interaction_data", {})
    history = state.get("conversation_memory", [])
    intent = state.get("current_tool", "simple_chat")

    # Build context to feed Groq chat completion
    context = {
        "hcp_name": current_data.get("hcp_name"),
        "specialty": current_data.get("specialty"),
        "hospital_clinic": current_data.get("hospital_clinic"),
        "tier": current_data.get("tier"),
        "interaction_date": str(current_data.get("interaction_date")) if current_data.get("interaction_date") else None,
        "sentiment": current_data.get("sentiment"),
        "products": current_data.get("products_discussed", []),
        "validation_status": state.get("validation_status")
    }

    # Collect applied changes for edit responses (from audit_log)
    applied_changes = {}
    for entry in state.get("audit_log", []):
        field = entry.get("field_name", "")
        new_val = entry.get("new_value", "")
        if field:
            applied_changes[field] = new_val

    chat_resp = groq_client.chat_response(user_msg, messages, context, intent=intent, applied_changes=applied_changes)
    new_message = {"sender": "assistant", "message": chat_resp}

    return {
        "messages": messages + [new_message],
        "tool_logs": state.get("tool_logs", []) + [{"step": "Response Generation Node", "status": "Generated CRM-style response"}]
    }

def audit_logging_node(state: CRMState, config: RunnableConfig) -> Dict[str, Any]:
    """Node 8: Record changes in database audit trail."""
    db: Session = config["configurable"]["db"]
    edits = state.get("audit_log", [])
    interaction_id = state.get("interaction_data", {}).get("id")
    
    if edits and interaction_id:
        for edit in edits:
            db_edit = InteractionEdit(
                interaction_id=interaction_id,
                field_name=edit["field_name"],
                old_value=edit["old_value"],
                new_value=edit["new_value"],
                edited_at=datetime.datetime.utcnow()
            )
            db.add(db_edit)
            
            # Write to audit_logs
            audit = AuditLog(
                action="UPDATE_FIELD",
                table_name="interactions",
                record_id=interaction_id,
                performed_by="AI_CRM_Assistant",
                details=f"Modified {edit['field_name']} from '{edit['old_value']}' to '{edit['new_value']}'"
            )
            db.add(audit)
        db.flush()
        
    return {
        "tool_logs": state.get("tool_logs", []) + [{"step": "Audit Logging Node", "status": f"Audited {len(edits)} database modifications"}]
    }

def database_persistence_node(state: CRMState, config: RunnableConfig) -> Dict[str, Any]:
    """Node 9: Write/Update active HCP CRM interaction record to MySQL."""
    db: Session = config["configurable"]["db"]
    data = state.get("interaction_data", {})
    intent = state.get("current_tool", "simple_chat")
    
    if not data or intent in ["simple_chat", "get_history"]:
        return {
            "tool_logs": state.get("tool_logs", []) + [{"step": "Database Persistence Node", "status": "No database updates needed"}]
        }
        
    # Resolve or create HCP Profile first
    hcp_name = data.get("hcp_name", "Unknown HCP")
    db_hcp = db.query(HCPProfile).filter(
        HCPProfile.name == hcp_name,
        HCPProfile.is_deleted == False
    ).first()
    
    if not db_hcp:
        db_hcp = HCPProfile(
            name=hcp_name,
            specialty=data.get("specialty", "General Practitioner"),
            hospital_clinic=data.get("hospital_clinic", "Local Hospital"),
            tier=data.get("tier", "B"),
            territory=data.get("territory", "General Territory")
        )
        db.add(db_hcp)
        db.flush()
        db.add(AuditLog(
            action="CREATE_HCP_PROFILE",
            table_name="hcp_profiles",
            record_id=db_hcp.id,
            performed_by="AI_CRM_Assistant",
            details=f"Auto-created HCP profile for {hcp_name}"
        ))
        
    # Create or update active interaction
    interaction_id = data.get("id")
    db_intr = None
    
    # Standard format conversion
    i_date = data.get("interaction_date")
    if isinstance(i_date, str):
        i_date = datetime.date.fromisoformat(i_date)
        
    f_date = data.get("follow_up_date")
    if isinstance(f_date, str):
        f_date = datetime.date.fromisoformat(f_date)
        
    if interaction_id:
        db_intr = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        
    if db_intr:
        # Update existing record
        db_intr.hcp_id = db_hcp.id
        db_intr.hcp_name = hcp_name
        db_intr.specialty = data.get("specialty", db_intr.specialty)
        db_intr.hospital_clinic = data.get("hospital_clinic", db_intr.hospital_clinic)
        db_intr.tier = data.get("tier", db_intr.tier)
        db_intr.territory = data.get("territory", db_intr.territory)
        db_intr.interaction_date = i_date if i_date else db_intr.interaction_date
        db_intr.interaction_type = data.get("interaction_type", db_intr.interaction_type)
        db_intr.visit_objective = data.get("visit_objective", db_intr.visit_objective)
        db_intr.key_discussion_points = data.get("key_discussion_points", db_intr.key_discussion_points)
        db_intr.objections_raised = data.get("objections_raised", db_intr.objections_raised)
        db_intr.sentiment = data.get("sentiment", db_intr.sentiment)
        db_intr.outcome = data.get("outcome", db_intr.outcome)
        db_intr.follow_up_required = data.get("follow_up_required", db_intr.follow_up_required)
        db_intr.follow_up_date = f_date if f_date else db_intr.follow_up_date
        db_intr.next_best_action = data.get("next_best_action", db_intr.next_best_action)
        db_intr.interaction_summary = data.get("interaction_summary", db_intr.interaction_summary)
        db_intr.validation_status = state.get("validation_status", db_intr.validation_status)
        db_intr.updated_at = datetime.datetime.utcnow()
        
        # Log to Tool Execution Logs
        db.add(ToolExecutionLog(
            interaction_id=db_intr.id,
            tool_name="Edit Interaction Tool",
            input_parameters=str(state.get("messages", [])[-1].get("message")),
            output_data=f"Updated record keys: {list(data.keys())}"
        ))
    else:
        # Create new record
        db_intr = Interaction(
            hcp_id=db_hcp.id,
            hcp_name=hcp_name,
            specialty=data.get("specialty", "General Practitioner"),
            hospital_clinic=data.get("hospital_clinic", "Local Hospital"),
            tier=data.get("tier", "B"),
            territory=data.get("territory", "General Territory"),
            interaction_date=i_date if i_date else datetime.date.today(),
            interaction_type=data.get("interaction_type", "In-Person"),
            visit_objective=data.get("visit_objective", "Product Detailing"),
            key_discussion_points=data.get("key_discussion_points"),
            objections_raised=data.get("objections_raised"),
            sentiment=data.get("sentiment", "Neutral"),
            outcome=data.get("outcome"),
            follow_up_required=data.get("follow_up_required", False),
            follow_up_date=f_date,
            next_best_action=data.get("next_best_action"),
            interaction_summary=data.get("interaction_summary"),
            validation_status=state.get("validation_status", "Pending"),
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
        )
        db.add(db_intr)
        db.flush() # Populate db_intr.id
        
        db.add(AuditLog(
            action="CREATE_INTERACTION",
            table_name="interactions",
            record_id=db_intr.id,
            performed_by="AI_CRM_Assistant",
            details=f"Created new interaction log with {hcp_name}"
        ))
        
        db.add(ToolExecutionLog(
            interaction_id=db_intr.id,
            tool_name="Log Interaction Tool",
            input_parameters=str(state.get("messages", [])[-1].get("message")),
            output_data=f"Created record ID: {db_intr.id}"
        ))

    # Re-sync products and materials
    if db_intr:
        # Delete old product relations
        db.query(InteractionProduct).filter(InteractionProduct.interaction_id == db_intr.id).delete()
        prods = data.get("products_discussed", [])
        if isinstance(prods, list):
            for prod in prods:
                db.add(InteractionProduct(interaction_id=db_intr.id, product_name=prod))

        # Delete old materials shared relations
        db.query(InteractionMaterial).filter(InteractionMaterial.interaction_id == db_intr.id).delete()
        mats = data.get("materials_shared", [])
        if isinstance(mats, list):
            for mat in mats:
                db.add(InteractionMaterial(interaction_id=db_intr.id, material_name=mat))
        
        # Save modifications in memory dict
        data["id"] = db_intr.id
        data["interaction_date"] = db_intr.interaction_date.isoformat()
        if db_intr.follow_up_date:
            data["follow_up_date"] = db_intr.follow_up_date.isoformat()
            
    db.commit()
    
    return {
        "interaction_data": data,
        "tool_logs": state.get("tool_logs", []) + [{"step": "Database Persistence Node", "status": f"Saved record ID {db_intr.id} successfully"}]
    }

# --- LANGGRAPH STATE GRAPH COMPILATION ---

def route_intent(state: CRMState) -> str:
    """Helper method for routing decision edges based on current tool intent."""
    intent = state.get("current_tool")
    if intent in ["log_new", "edit_existing", "get_history", "validate_form", "get_recommendation"]:
        return "tool_execution"
    return "response_generation"

def build_workflow() -> StateGraph:
    workflow = StateGraph(CRMState)
    
    # Add Nodes
    workflow.add_node("user_input", user_input_node)
    workflow.add_node("intent_classification", intent_classification_node)
    workflow.add_node("tool_execution", tool_execution_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("audit_logging", audit_logging_node)
    workflow.add_node("database_persistence", database_persistence_node)
    workflow.add_node("state_update", state_update_node)
    workflow.add_node("response_generation", response_generation_node)
    
    # Wire Edges
    workflow.set_entry_point("user_input")
    workflow.add_edge("user_input", "intent_classification")
    
    # Conditional edge route based on intent classification
    workflow.add_conditional_edges(
        "intent_classification",
        route_intent,
        {
            "tool_execution": "tool_execution",
            "response_generation": "response_generation"
        }
    )
    
    # Tool execution flow
    workflow.add_edge("tool_execution", "validation")
    workflow.add_edge("validation", "audit_logging")
    workflow.add_edge("audit_logging", "database_persistence")
    workflow.add_edge("database_persistence", "state_update")
    workflow.add_edge("state_update", "response_generation")
    
    workflow.add_edge("response_generation", END)
    
    return workflow.compile()

# Compile graph instance
agent_workflow = build_workflow()
