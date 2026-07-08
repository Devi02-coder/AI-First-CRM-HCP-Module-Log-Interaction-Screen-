import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(150), unique=True, nullable=False)
    role = Column(String(50), default="Representative")

class HCPProfile(Base):
    __tablename__ = "hcp_profiles"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), nullable=False, index=True)
    specialty = Column(String(100), nullable=False, index=True)
    hospital_clinic = Column(String(200), nullable=False)
    tier = Column(String(10), default="B") # Tier A, B, C
    territory = Column(String(100), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

class Interaction(Base):
    __tablename__ = "interactions"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hcp_id = Column(Integer, ForeignKey("hcp_profiles.id"), nullable=True)
    hcp_name = Column(String(150), nullable=False, index=True)
    specialty = Column(String(100), nullable=False)
    hospital_clinic = Column(String(200), nullable=False)
    tier = Column(String(10), default="B")
    territory = Column(String(100), nullable=False)
    interaction_date = Column(Date, nullable=False, index=True)
    interaction_type = Column(String(50), nullable=False) # In-Person, Video Call, Email, Phone
    visit_objective = Column(String(150), nullable=False)
    key_discussion_points = Column(Text, nullable=True)
    objections_raised = Column(Text, nullable=True)
    sentiment = Column(String(50), nullable=False)
    outcome = Column(Text, nullable=True)
    follow_up_required = Column(Boolean, default=False, nullable=False)
    follow_up_date = Column(Date, nullable=True)
    next_best_action = Column(Text, nullable=True)
    interaction_summary = Column(Text, nullable=True)
    validation_status = Column(String(50), default="Pending")
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    # Relationships
    hcp = relationship("HCPProfile")
    products = relationship("InteractionProduct", back_populates="interaction", cascade="all, delete-orphan")
    materials = relationship("InteractionMaterial", back_populates="interaction", cascade="all, delete-orphan")
    edits = relationship("InteractionEdit", back_populates="interaction", cascade="all, delete-orphan")
    follow_ups = relationship("FollowUpTask", back_populates="interaction", cascade="all, delete-orphan")

class InteractionProduct(Base):
    __tablename__ = "interaction_products"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    interaction_id = Column(Integer, ForeignKey("interactions.id"), nullable=False)
    product_name = Column(String(100), nullable=False, index=True)

    interaction = relationship("Interaction", back_populates="products")

class InteractionMaterial(Base):
    __tablename__ = "interaction_materials"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    interaction_id = Column(Integer, ForeignKey("interactions.id"), nullable=False)
    material_name = Column(String(150), nullable=False, index=True)

    interaction = relationship("Interaction", back_populates="materials")

class InteractionEdit(Base):
    __tablename__ = "interaction_edits"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    interaction_id = Column(Integer, ForeignKey("interactions.id"), nullable=False)
    field_name = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    edited_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    interaction = relationship("Interaction", back_populates="edits")

class FollowUpTask(Base):
    __tablename__ = "follow_up_tasks"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    interaction_id = Column(Integer, ForeignKey("interactions.id"), nullable=False)
    description = Column(Text, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(50), default="Pending") # Pending, Completed, Cancelled

    interaction = relationship("Interaction", back_populates="follow_ups")

class AgentMemory(Base):
    __tablename__ = "agent_memory"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hcp_name = Column(String(150), nullable=False, index=True)
    context_key = Column(String(100), nullable=False)
    context_value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sender = Column(String(50), nullable=False) # user, assistant
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class ToolExecutionLog(Base):
    __tablename__ = "tool_execution_logs"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    interaction_id = Column(Integer, ForeignKey("interactions.id"), nullable=True)
    tool_name = Column(String(100), nullable=False)
    input_parameters = Column(Text, nullable=True)
    output_data = Column(Text, nullable=True)
    executed_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    action = Column(String(100), nullable=False)
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=False)
    performed_by = Column(String(100), default="System")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    details = Column(Text, nullable=True)
