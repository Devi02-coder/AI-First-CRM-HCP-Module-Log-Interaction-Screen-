"""
Comprehensive Database Seeder for HCP CRM
Populates all 11 tables with rich pharma CRM sample data.
Run: py -3.13 seed_data.py
"""
import sys, os, datetime
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import (
    User, HCPProfile, Interaction, InteractionProduct, InteractionMaterial,
    InteractionEdit, FollowUpTask, AgentMemory, ChatMessage,
    ToolExecutionLog, AuditLog
)
from app.database import Base

DB_URL = "mysql+pymysql://root:2003@localhost:3306/hcp_crm"
engine = create_engine(DB_URL, pool_pre_ping=True)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
db = Session()

TODAY = datetime.date.today()
NOW  = datetime.datetime.utcnow()

def d(days_ago): return TODAY - datetime.timedelta(days=days_ago)
def dt(days_ago): return NOW - datetime.timedelta(days=days_ago)

try:
    # ── 1. USERS ────────────────────────────────────────────────
    print("Seeding users...")
    users = [
        User(username="rep_muthu",   email="muthu@pharmaco.com",   role="Medical Representative"),
        User(username="rep_priya",   email="priya@pharmaco.com",   role="Medical Representative"),
        User(username="rep_arjun",   email="arjun@pharmaco.com",   role="Medical Representative"),
        User(username="mgr_alex",    email="alex@pharmaco.com",    role="Regional Manager"),
        User(username="mgr_kavya",   email="kavya@pharmaco.com",   role="Area Business Manager"),
    ]
    db.add_all(users); db.flush()
    print(f"  Added {len(users)} users")

    # ── 2. HCP PROFILES ─────────────────────────────────────────
    print("Seeding HCP profiles...")
    hcps = [
        HCPProfile(name="Dr. Sarah Johnson",    specialty="Cardiologist",          hospital_clinic="Apollo Hospital",         tier="A", territory="Metro North"),
        HCPProfile(name="Dr. John Doe",         specialty="Neurologist",            hospital_clinic="City Medical Center",     tier="B", territory="Metro West"),
        HCPProfile(name="Dr. Lisa Ray",         specialty="Orthopedic Specialist",  hospital_clinic="Grace Clinic",            tier="C", territory="South Zone"),
        HCPProfile(name="Dr. Ramesh Kumar",     specialty="General Physician",      hospital_clinic="Fortis Hospital",         tier="A", territory="Metro East"),
        HCPProfile(name="Dr. Anjali Mehta",     specialty="Oncologist",             hospital_clinic="Manipal Cancer Center",   tier="A", territory="Central Hub"),
        HCPProfile(name="Dr. Vikram Nair",      specialty="Cardiologist",           hospital_clinic="Medanta Hospital",        tier="B", territory="North Zone"),
        HCPProfile(name="Dr. Priya Sharma",     specialty="Diabetologist",          hospital_clinic="Max Healthcare",          tier="B", territory="Metro North"),
        HCPProfile(name="Dr. Arun Patel",       specialty="Pulmonologist",          hospital_clinic="Sterling Hospital",       tier="C", territory="West Zone"),
        HCPProfile(name="Dr. Meena Iyer",       specialty="Neurologist",            hospital_clinic="Kovai Medical Center",    tier="A", territory="South Zone"),
        HCPProfile(name="Dr. Suresh Reddy",     specialty="Cardiologist",           hospital_clinic="KIMS Hospital",           tier="B", territory="Metro South"),
    ]
    db.add_all(hcps); db.flush()
    print(f"  Added {len(hcps)} HCP profiles")

    # ── 3. INTERACTIONS ─────────────────────────────────────────
    print("Seeding interactions...")
    interaction_data = [
        # Dr. Sarah Johnson - 3 interactions
        dict(hcp=hcps[0], date=d(30), itype="In-Person",   obj="Product Detailing",      sentiment="Positive", prods=["CardioMax","HeartPlus"],  mats=["CardioMax Brochure","Efficacy Study"], disc="Reviewed CardioMax Phase III trial results. Doctor very impressed with 35% reduction in cardiac events.", obj_raised="Mild concern about elderly dosing",         outcome="Agreed to prescribe for new patients.", follow=True,  fdate=d(23), nba="Send Phase IV trial enrollment details.", summary="Strong positive engagement. CardioMax to be adopted in practice.", validation="Valid"),
        dict(hcp=hcps[0], date=d(15), itype="Video Call",  obj="Follow-Up",              sentiment="Positive", prods=["CardioMax"],              mats=["Dosing Guide"],               disc="Follow-up on initial prescription outcomes. 3 patients already started.", obj_raised=None,                                   outcome="Wants 10 more units of starter pack.",  follow=True,  fdate=d(8),  nba="Arrange peer discussion event.",          summary="CardioMax adoption progressing well. Tier A relationship strengthened.", validation="Valid"),
        dict(hcp=hcps[0], date=d(2),  itype="In-Person",   obj="Clinical Data Review",   sentiment="Positive", prods=["CardioMax","LipidBloc"],  mats=["Clinical Trial PDF","Safety Report"], disc="Presented LipidBloc alongside CardioMax for combo therapy.", obj_raised="Insurance coverage for LipidBloc",    outcome="Interested in combo therapy protocol.",  follow=True,  fdate=d(-5), nba="Share insurance reimbursement guide.",     summary="Expanded portfolio discussion. Combo therapy interest noted.", validation="Valid"),
        # Dr. John Doe - 2 interactions
        dict(hcp=hcps[1], date=d(25), itype="In-Person",   obj="Product Introduction",   sentiment="Neutral",  prods=["NeuroMax"],               mats=["NeuroMax Brochure"],          disc="First visit. Introduced NeuroMax for neuropathic pain.",      obj_raised="Skeptical about efficacy vs. current treatment", outcome="Asked for peer-reviewed papers.",       follow=True,  fdate=d(18), nba="Share peer comparison data within 3 days.", summary="Initial cold visit converted to interest. Follow-up critical.", validation="Valid"),
        dict(hcp=hcps[1], date=d(10), itype="In-Person",   obj="Efficacy Discussion",    sentiment="Positive", prods=["NeuroMax"],               mats=["Peer Review Study","Patient Case Studies"], disc="Shared peer-review study. Doctor reviewed 2 case studies.", obj_raised=None,                                   outcome="Agreed to trial NeuroMax on 2 patients.",follow=True,  fdate=d(3),  nba="Arrange patient monitoring check-in.",    summary="Successfully converted skeptic to advocate. Key win.", validation="Valid"),
        # Dr. Lisa Ray - 2 interactions
        dict(hcp=hcps[2], date=d(20), itype="In-Person",   obj="Product Detailing",      sentiment="Negative", prods=["OsteoCare"],              mats=["OsteoCare Brochure"],         disc="OsteoCare for post-surgical recovery. Doctor prefers competitor.",obj_raised="Strong preference for competitor brand",outcome="No immediate adoption. Needs more evidence.", follow=False, fdate=None,  nba="Schedule Medical Director presentation.",summary="Tough call. Competitor entrenched. Strategic escalation needed.", validation="Valid"),
        dict(hcp=hcps[2], date=d(5),  itype="Phone",       obj="Relationship Maintenance",sentiment="Neutral",  prods=["OsteoCare"],              mats=["Comparative Efficacy Chart"], disc="Quick call. Shared comparative efficacy chart by email.",      obj_raised="Still evaluating",                             outcome="Will consider for next quarter.",         follow=True,  fdate=d(-7), nba="Send Q3 promotional pricing sheet.",      summary="Slow progress. Needs sustained engagement over next 2 months.", validation="Valid"),
        # Dr. Ramesh Kumar - 2 interactions
        dict(hcp=hcps[3], date=d(12), itype="In-Person",   obj="Product Detailing",      sentiment="Positive", prods=["CardioMax","GastroShield"],mats=["Combo Brochure","Clinical Data"],disc="Discussed both cardiac and GI protection in high-risk patients.",obj_raised=None,                                    outcome="Ordered 20 units of CardioMax.",          follow=True,  fdate=d(5),  nba="Deliver samples and confirm order.",      summary="High-volume Tier A. Excellent adoption of full portfolio.", validation="Valid"),
        dict(hcp=hcps[3], date=d(1),  itype="In-Person",   obj="Account Review",         sentiment="Positive", prods=["CardioMax","LipidBloc","GastroShield"],mats=["Q2 Report"],   disc="Reviewed Q2 prescription data. Very satisfied with patient outcomes.", obj_raised="Needs bulk pricing for GastroShield", outcome="Committed to continued prescription.",    follow=True,  fdate=d(-10),nba="Provide bulk pricing proposal.",         summary="Key account secured for Q3. Pricing discussion pending.", validation="Valid"),
        # Dr. Anjali Mehta - 1 interaction
        dict(hcp=hcps[4], date=d(7),  itype="In-Person",   obj="Product Introduction",   sentiment="Positive", prods=["OncoShield"],              mats=["Phase III Data","MOA Slide Deck"],disc="Introduced OncoShield for adjuvant therapy in breast cancer.",obj_raised="Cost of therapy for uninsured patients",outcome="Will present at tumor board next week.",  follow=True,  fdate=d(-3), nba="Prepare tumor board presentation deck.",summary="KOL interest secured. Tumor board presentation is major opportunity.", validation="Valid"),
        # Dr. Vikram Nair - 1 interaction
        dict(hcp=hcps[5], date=d(18), itype="Video Call",  obj="Product Detailing",      sentiment="Neutral",  prods=["HeartPlus"],              mats=["HeartPlus Overview"],          disc="Introduced HeartPlus for CHF management.",                    obj_raised="Prefers guideline-only medications",            outcome="Needs clinical guideline endorsement.",  follow=True,  fdate=d(11), nba="Share ACC/AHA guideline inclusion evidence.",summary="Conservative prescriber. Guideline data is key.", validation="Valid"),
        # Dr. Priya Sharma - 1 interaction
        dict(hcp=hcps[6], date=d(9),  itype="In-Person",   obj="Product Detailing",      sentiment="Positive", prods=["InsulinPrime"],            mats=["Dosing Algorithm","Patient Log"],disc="Discussed InsulinPrime for T2DM management. Doctor manages 200+ diabetic patients.", obj_raised=None,              outcome="Very interested. Requested samples.",    follow=True,  fdate=d(2),  nba="Send 30 sample units for patient trial.", summary="High-potential prescriber with large diabetic patient base.", validation="Valid"),
        # Dr. Meena Iyer - 1 interaction
        dict(hcp=hcps[8], date=d(14), itype="In-Person",   obj="Clinical Data Review",   sentiment="Positive", prods=["NeuroMax"],               mats=["NeuroMax Clinical Study","MRI Correlation Data"],disc="Detailed clinical review of NeuroMax MRI correlation study.",obj_raised=None,                        outcome="Will recommend to neurology colleagues.", follow=True,  fdate=d(7),  nba="Organize KOL speaker event.",           summary="Top KOL engagement. Peer influence strategy initiated.", validation="Valid"),
        # Dr. Suresh Reddy - 1 interaction
        dict(hcp=hcps[9], date=d(22), itype="In-Person",   obj="Product Detailing",      sentiment="Neutral",  prods=["CardioMax"],              mats=["CardioMax Brochure"],          disc="Standard product detailing visit.",                           obj_raised="Waiting for more real-world evidence",         outcome="Will monitor market feedback.",          follow=False, fdate=None,  nba="Share post-marketing surveillance report.",summary="Lukewarm reception. Real-world data needed.", validation="Pending"),
    ]

    interactions = []
    for item in interaction_data:
        hcp = item["hcp"]
        intr = Interaction(
            hcp_id=hcp.id, hcp_name=hcp.name, specialty=hcp.specialty,
            hospital_clinic=hcp.hospital_clinic, tier=hcp.tier, territory=hcp.territory,
            interaction_date=item["date"], interaction_type=item["itype"],
            visit_objective=item["obj"], key_discussion_points=item["disc"],
            objections_raised=item.get("obj_raised"),
            sentiment=item["sentiment"], outcome=item["outcome"],
            follow_up_required=item["follow"], follow_up_date=item.get("fdate"),
            next_best_action=item["nba"], interaction_summary=item["summary"],
            validation_status=item["validation"],
            created_at=dt(30), updated_at=dt(1)
        )
        db.add(intr); db.flush()
        for p in item["prods"]:
            db.add(InteractionProduct(interaction_id=intr.id, product_name=p))
        for m in item["mats"]:
            db.add(InteractionMaterial(interaction_id=intr.id, material_name=m))
        interactions.append(intr)
    db.flush()
    print(f"  Added {len(interactions)} interactions with products and materials")

    # ── 4. INTERACTION EDITS ────────────────────────────────────
    print("Seeding interaction edits...")
    edits = [
        InteractionEdit(interaction_id=interactions[0].id, field_name="sentiment",       old_value="Neutral",   new_value="Positive",  edited_at=dt(28)),
        InteractionEdit(interaction_id=interactions[0].id, field_name="follow_up_date",  old_value="2026-06-20",new_value="2026-06-23", edited_at=dt(27)),
        InteractionEdit(interaction_id=interactions[1].id, field_name="outcome",         old_value="Pending",   new_value="Agreed to prescribe for new patients.", edited_at=dt(14)),
        InteractionEdit(interaction_id=interactions[3].id, field_name="sentiment",       old_value="Negative",  new_value="Neutral",   edited_at=dt(22)),
        InteractionEdit(interaction_id=interactions[5].id, field_name="validation_status",old_value="Pending",  new_value="Valid",     edited_at=dt(19)),
        InteractionEdit(interaction_id=interactions[7].id, field_name="tier",            old_value="B",         new_value="A",         edited_at=dt(10)),
        InteractionEdit(interaction_id=interactions[9].id, field_name="next_best_action",old_value="Send brochure", new_value="Prepare tumor board presentation deck.", edited_at=dt(6)),
    ]
    db.add_all(edits)
    print(f"  Added {len(edits)} interaction edits")

    # ── 5. FOLLOW-UP TASKS ──────────────────────────────────────
    print("Seeding follow-up tasks...")
    tasks = [
        FollowUpTask(interaction_id=interactions[0].id,  description="Send CardioMax Phase IV trial enrollment documents to Dr. Sarah Johnson", due_date=d(-2),  status="Pending"),
        FollowUpTask(interaction_id=interactions[1].id,  description="Arrange peer KOL discussion event for Apollo Hospital",                   due_date=d(-5),  status="Completed"),
        FollowUpTask(interaction_id=interactions[2].id,  description="Share insurance reimbursement guide for LipidBloc combo therapy",         due_date=d(2),   status="Pending"),
        FollowUpTask(interaction_id=interactions[3].id,  description="Send NeuroMax peer comparison data to Dr. John Doe within 3 days",        due_date=d(-10), status="Completed"),
        FollowUpTask(interaction_id=interactions[4].id,  description="Arrange patient monitoring check-in call for Dr. Doe's NeuroMax trials",  due_date=d(-1),  status="Pending"),
        FollowUpTask(interaction_id=interactions[5].id,  description="Schedule Medical Director presentation at Grace Clinic",                   due_date=d(5),   status="Pending"),
        FollowUpTask(interaction_id=interactions[7].id,  description="Deliver CardioMax samples and confirm order for Dr. Ramesh Kumar",         due_date=d(0),   status="Pending"),
        FollowUpTask(interaction_id=interactions[9].id,  description="Prepare tumor board presentation deck for Dr. Anjali Mehta",              due_date=d(2),   status="Pending"),
        FollowUpTask(interaction_id=interactions[11].id, description="Send ACC/AHA guideline inclusion evidence to Dr. Vikram Nair",             due_date=d(4),   status="Pending"),
        FollowUpTask(interaction_id=interactions[12].id, description="Send 30 InsulinPrime sample units to Max Healthcare for Dr. Priya Sharma",due_date=d(1),   status="Pending"),
    ]
    db.add_all(tasks)
    print(f"  Added {len(tasks)} follow-up tasks")

    # ── 6. AGENT MEMORY ─────────────────────────────────────────
    print("Seeding agent memory...")
    memories = [
        AgentMemory(hcp_name="Dr. Sarah Johnson", context_key="preferred_products",  context_value="CardioMax, LipidBloc", updated_at=dt(2)),
        AgentMemory(hcp_name="Dr. Sarah Johnson", context_key="key_objections",      context_value="Elderly dosing concerns for CardioMax", updated_at=dt(2)),
        AgentMemory(hcp_name="Dr. Sarah Johnson", context_key="relationship_level",  context_value="Champion", updated_at=dt(2)),
        AgentMemory(hcp_name="Dr. John Doe",      context_key="preferred_products",  context_value="NeuroMax", updated_at=dt(10)),
        AgentMemory(hcp_name="Dr. John Doe",      context_key="key_objections",      context_value="Needs peer-reviewed evidence before adopting", updated_at=dt(10)),
        AgentMemory(hcp_name="Dr. Ramesh Kumar",  context_key="preferred_products",  context_value="CardioMax, GastroShield, LipidBloc", updated_at=dt(1)),
        AgentMemory(hcp_name="Dr. Ramesh Kumar",  context_key="relationship_level",  context_value="Champion", updated_at=dt(1)),
        AgentMemory(hcp_name="Dr. Lisa Ray",      context_key="competitor_info",     context_value="Strongly uses BoneGuard by CompetitorX", updated_at=dt(5)),
        AgentMemory(hcp_name="Dr. Anjali Mehta",  context_key="key_interest",        context_value="OncoShield Phase III data. Tumor board involvement.", updated_at=dt(7)),
        AgentMemory(hcp_name="Dr. Priya Sharma",  context_key="patient_volume",      context_value="200+ T2DM patients per month", updated_at=dt(9)),
    ]
    db.add_all(memories)
    print(f"  Added {len(memories)} agent memory entries")

    # ── 7. CHAT MESSAGES ─────────────────────────────────────────
    print("Seeding chat messages...")
    chats = [
        ChatMessage(sender="assistant", message="Hello! I am your AI CRM Assistant. How can I help you today?",                                                              timestamp=dt(5)),
        ChatMessage(sender="user",      message="Met Dr. Sarah Johnson today at Apollo Hospital. Discussed CardioMax and HeartPlus. Very positive. Follow up next Tuesday.", timestamp=dt(5)),
        ChatMessage(sender="assistant", message="I have logged a new interaction with Dr. Sarah Johnson at Apollo Hospital. Entities extracted and form populated. Validation passed.",timestamp=dt(5)),
        ChatMessage(sender="user",      message="Change sentiment to Positive",                                                                                               timestamp=dt(4)),
        ChatMessage(sender="assistant", message="I have updated the sentiment field to Positive for the active interaction with Dr. Sarah Johnson. Audit trail recorded.",    timestamp=dt(4)),
        ChatMessage(sender="user",      message="Show history for Dr. John Doe",                                                                                              timestamp=dt(3)),
        ChatMessage(sender="assistant", message="Here are 2 previous interactions with Dr. John Doe at City Medical Center. First visit on 2026-06-13 and follow-up on 2026-06-28.",timestamp=dt(3)),
        ChatMessage(sender="user",      message="Validate the current form",                                                                                                  timestamp=dt(2)),
        ChatMessage(sender="assistant", message="CRM Validation complete. The record is VALID. All mandatory fields are populated and constraints are satisfied.",             timestamp=dt(2)),
        ChatMessage(sender="user",      message="What is the next best action for Dr. Ramesh Kumar?",                                                                         timestamp=dt(1)),
        ChatMessage(sender="assistant", message="Next Best Action for Dr. Ramesh Kumar: Provide bulk pricing proposal for GastroShield. Schedule Q3 account review by end of month.", timestamp=dt(1)),
    ]
    db.add_all(chats)
    print(f"  Added {len(chats)} chat messages")

    # ── 8. TOOL EXECUTION LOGS ──────────────────────────────────
    print("Seeding tool execution logs...")
    tool_logs = [
        ToolExecutionLog(interaction_id=interactions[0].id, tool_name="Log Interaction Tool",         input_parameters="Met Dr. Sarah Johnson at Apollo...", output_data='{"hcp_name":"Dr. Sarah Johnson","sentiment":"Positive"}', executed_at=dt(30)),
        ToolExecutionLog(interaction_id=interactions[0].id, tool_name="Interaction Summary Tool",      input_parameters='{"hcp_name":"Dr. Sarah Johnson"}',  output_data="Strong positive engagement. CardioMax adoption planned.",     executed_at=dt(30)),
        ToolExecutionLog(interaction_id=interactions[0].id, tool_name="Next Best Action Tool",         input_parameters='{"products":["CardioMax"],"sentiment":"Positive"}', output_data="Send Phase IV trial enrollment details.",       executed_at=dt(30)),
        ToolExecutionLog(interaction_id=interactions[0].id, tool_name="CRM Validation Tool",           input_parameters='{"hcp_name":"Dr. Sarah Johnson"}',  output_data='{"is_valid":true,"validation_status":"Valid"}',             executed_at=dt(30)),
        ToolExecutionLog(interaction_id=interactions[1].id, tool_name="Edit Interaction Tool",         input_parameters="Change sentiment to Positive",       output_data='{"sentiment":"Positive"}',                                  executed_at=dt(14)),
        ToolExecutionLog(interaction_id=interactions[3].id, tool_name="Log Interaction Tool",          input_parameters="Met Dr. John Doe at City Medical...", output_data='{"hcp_name":"Dr. John Doe","sentiment":"Neutral"}',        executed_at=dt(25)),
        ToolExecutionLog(interaction_id=interactions[4].id, tool_name="HCP Context Retrieval Tool",    input_parameters='{"hcp_name":"Dr. John Doe"}',        output_data='[{"date":"2026-06-13","sentiment":"Neutral"}]',             executed_at=dt(10)),
        ToolExecutionLog(interaction_id=interactions[7].id, tool_name="Log Interaction Tool",          input_parameters="Visited Dr. Ramesh Kumar at Fortis...",output_data='{"hcp_name":"Dr. Ramesh Kumar","tier":"A"}',             executed_at=dt(12)),
        ToolExecutionLog(interaction_id=interactions[9].id, tool_name="Interaction Summary Tool",      input_parameters='{"hcp_name":"Dr. Anjali Mehta"}',    output_data="KOL tumor board interest secured.",                         executed_at=dt(7)),
        ToolExecutionLog(interaction_id=interactions[12].id,tool_name="Next Best Action Tool",         input_parameters='{"products":["InsulinPrime"],"sentiment":"Positive"}', output_data="Send 30 sample units for patient trial.", executed_at=dt(9)),
    ]
    db.add_all(tool_logs)
    print(f"  Added {len(tool_logs)} tool execution logs")

    # ── 9. AUDIT LOGS ───────────────────────────────────────────
    print("Seeding audit logs...")
    audit_logs = [
        AuditLog(action="CREATE_HCP_PROFILE",  table_name="hcp_profiles",  record_id=hcps[0].id,  performed_by="AI_CRM_Assistant", timestamp=dt(30), details="Auto-created HCP profile for Dr. Sarah Johnson"),
        AuditLog(action="CREATE_INTERACTION",  table_name="interactions",  record_id=interactions[0].id, performed_by="AI_CRM_Assistant", timestamp=dt(30), details="Logged new interaction via Log Interaction Tool"),
        AuditLog(action="UPDATE_FIELD",        table_name="interactions",  record_id=interactions[0].id, performed_by="AI_CRM_Assistant", timestamp=dt(28), details="Modified sentiment from 'Neutral' to 'Positive'"),
        AuditLog(action="CREATE_HCP_PROFILE",  table_name="hcp_profiles",  record_id=hcps[1].id,  performed_by="AI_CRM_Assistant", timestamp=dt(25), details="Auto-created HCP profile for Dr. John Doe"),
        AuditLog(action="CREATE_INTERACTION",  table_name="interactions",  record_id=interactions[3].id, performed_by="AI_CRM_Assistant", timestamp=dt(25), details="Logged new interaction via Log Interaction Tool"),
        AuditLog(action="UPDATE_FIELD",        table_name="interactions",  record_id=interactions[3].id, performed_by="AI_CRM_Assistant", timestamp=dt(22), details="Modified sentiment from 'Negative' to 'Neutral'"),
        AuditLog(action="CREATE_INTERACTION",  table_name="interactions",  record_id=interactions[5].id, performed_by="AI_CRM_Assistant", timestamp=dt(20), details="Logged new interaction with Dr. Lisa Ray"),
        AuditLog(action="CREATE_HCP_PROFILE",  table_name="hcp_profiles",  record_id=hcps[3].id,  performed_by="AI_CRM_Assistant", timestamp=dt(12), details="Auto-created HCP profile for Dr. Ramesh Kumar"),
        AuditLog(action="CREATE_INTERACTION",  table_name="interactions",  record_id=interactions[7].id, performed_by="AI_CRM_Assistant", timestamp=dt(12), details="Logged new interaction via Log Interaction Tool"),
        AuditLog(action="UPDATE_FIELD",        table_name="hcp_profiles",  record_id=hcps[3].id,  performed_by="AI_CRM_Assistant", timestamp=dt(10), details="Updated tier from B to A for Dr. Ramesh Kumar"),
        AuditLog(action="CREATE_INTERACTION",  table_name="interactions",  record_id=interactions[9].id, performed_by="AI_CRM_Assistant", timestamp=dt(7), details="Logged new interaction with Dr. Anjali Mehta"),
        AuditLog(action="CREATE_INTERACTION",  table_name="interactions",  record_id=interactions[12].id,performed_by="AI_CRM_Assistant", timestamp=dt(9), details="Logged new interaction with Dr. Priya Sharma"),
        AuditLog(action="VALIDATE_RECORD",     table_name="interactions",  record_id=interactions[0].id, performed_by="AI_CRM_Assistant", timestamp=dt(2), details="CRM validation passed. Status set to Valid."),
        AuditLog(action="CREATE_INTERACTION",  table_name="interactions",  record_id=interactions[1].id, performed_by="AI_CRM_Assistant", timestamp=dt(15), details="Follow-up interaction logged with Dr. Sarah Johnson"),
    ]
    db.add_all(audit_logs)
    print(f"  Added {len(audit_logs)} audit logs")

    db.commit()

    # ── SUMMARY ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  DATABASE SEEDING COMPLETE!")
    print("=" * 60)

    from sqlalchemy import text
    for tbl in ["users","hcp_profiles","interactions","interaction_products","interaction_materials","interaction_edits","follow_up_tasks","agent_memory","chat_messages","tool_execution_logs","audit_logs"]:
        cnt = db.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
        print(f"  {tbl:<30} : {cnt} records")
    print("=" * 60)

except Exception as e:
    db.rollback()
    import traceback; traceback.print_exc()
    print(f"\n[ERROR] Seeding failed: {e}")
finally:
    db.close()
