from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime

# Message Schemas
class MessageBase(BaseModel):
    sender: str = Field(..., description="Either 'user' or 'assistant'")
    message: str = Field(..., description="Message text content")

class MessageCreate(MessageBase):
    pass

class ChatMessageOut(MessageBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# Product and Material schemas
class ProductBase(BaseModel):
    product_name: str

class ProductOut(ProductBase):
    id: int
    interaction_id: int
    class Config:
        from_attributes = True

class MaterialBase(BaseModel):
    material_name: str

class MaterialOut(MaterialBase):
    id: int
    interaction_id: int
    class Config:
        from_attributes = True

# Follow up task schemas
class FollowUpBase(BaseModel):
    description: str
    due_date: date
    status: str = "Pending"

class FollowUpOut(FollowUpBase):
    id: int
    interaction_id: int
    class Config:
        from_attributes = True

# Interaction Schemas
class InteractionBase(BaseModel):
    hcp_name: str
    specialty: str
    hospital_clinic: str
    tier: Optional[str] = "B"
    territory: str
    interaction_date: date
    interaction_type: str
    visit_objective: str
    key_discussion_points: Optional[str] = None
    objections_raised: Optional[str] = None
    sentiment: str
    outcome: Optional[str] = None
    follow_up_required: bool = False
    follow_up_date: Optional[date] = None
    next_best_action: Optional[str] = None
    interaction_summary: Optional[str] = None
    validation_status: Optional[str] = "Pending"

class InteractionCreate(InteractionBase):
    products: List[str] = []
    materials: List[str] = []

class InteractionUpdate(BaseModel):
    hcp_name: Optional[str] = None
    specialty: Optional[str] = None
    hospital_clinic: Optional[str] = None
    tier: Optional[str] = None
    territory: Optional[str] = None
    interaction_date: Optional[date] = None
    interaction_type: Optional[str] = None
    visit_objective: Optional[str] = None
    key_discussion_points: Optional[str] = None
    objections_raised: Optional[str] = None
    sentiment: Optional[str] = None
    outcome: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[date] = None
    next_best_action: Optional[str] = None
    interaction_summary: Optional[str] = None
    validation_status: Optional[str] = None
    products: Optional[List[str]] = None
    materials: Optional[List[str]] = None

class InteractionOut(InteractionBase):
    id: int
    hcp_id: Optional[int] = None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    products: List[ProductOut] = []
    materials: List[MaterialOut] = []
    follow_ups: List[FollowUpOut] = []

    class Config:
        from_attributes = True

# Tool Execution Logs
class ToolExecutionLogOut(BaseModel):
    id: int
    interaction_id: Optional[int] = None
    tool_name: str
    input_parameters: Optional[str] = None
    output_data: Optional[str] = None
    executed_at: datetime

    class Config:
        from_attributes = True

# Audit Logs
class AuditLogOut(BaseModel):
    id: int
    action: str
    table_name: str
    record_id: int
    performed_by: str
    timestamp: datetime
    details: Optional[str] = None

    class Config:
        from_attributes = True

# Chat Request / Response Schemas
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    interaction_data: Optional[dict] = None
    current_tool: Optional[str] = None
    validation_status: Optional[str] = None
    tool_execution_logs: List[dict] = []

# Validation schemas
class ValidationIssue(BaseModel):
    field: str
    message: str
    severity: str  # "error" or "warning"

class ValidationReport(BaseModel):
    is_valid: bool
    validation_status: str
    issues: List[ValidationIssue] = []

# Next Best Action Schemas
class NextBestActionRequest(BaseModel):
    products: List[str]
    sentiment: str
    objections: Optional[str] = None

class NextBestActionResponse(BaseModel):
    next_best_action: str
    recommended_materials: List[str]
    suggested_topics: List[str]
