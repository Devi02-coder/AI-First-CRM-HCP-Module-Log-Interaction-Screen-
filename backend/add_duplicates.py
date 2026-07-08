"""
Script to add duplicate/additional values into the database tables.
This demonstrates handling duplicate columns and multiple entries per entity.
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

DB_URL = "mysql+pymysql://root:2003@localhost:3306/hcp_crm"
engine = create_engine(DB_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)
db = Session()

TODAY = datetime.date.today()
NOW  = datetime.datetime.utcnow()

try:
    print("Adding duplicate/additional values to tables...")

    # 1. Add a user with a similar name but unique email
    duplicate_user = User(username="rep_muthu_2", email="muthu.duplicate@pharmaco.com", role="Medical Representative")
    db.add(duplicate_user)
    db.flush()
    print("  [OK] Added duplicate/alternative User record.")

    # 2. Add an HCP profile with the exact same name, specialty, and hospital (simulating duplicate/multiple clinic locations)
    duplicate_hcp = HCPProfile(
        name="Dr. Sarah Johnson",
        specialty="Cardiologist",
        hospital_clinic="Apollo Hospital (Secunderabad Branch)",
        tier="A",
        territory="Metro North"
    )
    db.add(duplicate_hcp)
    db.flush()
    print("  [OK] Added duplicate/alternative HCP Profile for Dr. Sarah Johnson at a different clinic.")

    # 3. Add duplicate interactions for Dr. Sarah Johnson to populate history
    duplicate_interaction = Interaction(
        hcp_id=duplicate_hcp.id,
        hcp_name=duplicate_hcp.name,
        specialty=duplicate_hcp.specialty,
        hospital_clinic=duplicate_hcp.hospital_clinic,
        tier=duplicate_hcp.tier,
        territory=duplicate_hcp.territory,
        interaction_date=TODAY,
        interaction_type="In-Person",
        visit_objective="Product Detailing",
        key_discussion_points="Discussed CardioMax efficacy and safety studies again.",
        objections_raised="Price is high for some patients.",
        sentiment="Positive",
        outcome="Agreed to prescribe to 5 new patients.",
        follow_up_required=True,
        follow_up_date=TODAY + datetime.timedelta(days=7),
        next_best_action="Deliver patient starter kits.",
        interaction_summary="Duplicate interaction logged to verify historical view.",
        validation_status="Valid"
    )
    db.add(duplicate_interaction)
    db.flush()
    print("  [OK] Added duplicate Interaction record.")

    # 4. Add duplicate products and materials
    db.add(InteractionProduct(interaction_id=duplicate_interaction.id, product_name="CardioMax"))
    db.add(InteractionMaterial(interaction_id=duplicate_interaction.id, material_name="CardioMax Brochure"))
    print("  [OK] Added duplicate InteractionProduct and InteractionMaterial records.")

    # 5. Add duplicate follow-up tasks
    db.add(FollowUpTask(interaction_id=duplicate_interaction.id, description="Deliver patient starter kits.", due_date=TODAY + datetime.timedelta(days=7), status="Pending"))
    print("  [OK] Added duplicate FollowUpTask.")

    # 6. Add duplicate agent memory
    db.add(AgentMemory(hcp_name="Dr. Sarah Johnson", context_key="preferred_products", context_value="CardioMax", updated_at=NOW))
    print("  [OK] Added duplicate AgentMemory.")

    # 7. Add duplicate chat messages
    db.add(ChatMessage(sender="user", message="Met Dr. Sarah Johnson today at Apollo Hospital. Discussed CardioMax.", timestamp=NOW))
    print("  [OK] Added duplicate ChatMessage.")

    # 8. Add duplicate tool logs
    db.add(ToolExecutionLog(interaction_id=duplicate_interaction.id, tool_name="Log Interaction Tool", input_parameters="Sarah Johnson CardioMax", output_data="Success", executed_at=NOW))
    print("  [OK] Added duplicate ToolExecutionLog.")

    # 9. Add duplicate audit logs
    db.add(AuditLog(action="CREATE_INTERACTION", table_name="interactions", record_id=duplicate_interaction.id, performed_by="AI_CRM_Assistant", timestamp=NOW, details="Logged duplicate interaction record"))
    print("  [OK] Added duplicate AuditLog.")

    db.commit()
    print("All duplicate/additional records successfully committed!")

except Exception as e:
    db.rollback()
    print(f"Error adding duplicates: {e}")
finally:
    db.close()
