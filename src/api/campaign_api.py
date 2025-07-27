"""
REST API for Campaign Management

This module provides FastAPI endpoints for campaign management operations including:
- CRUD operations
- Bulk operations
- State management
- Analytics and history
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import logging

from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from campaign_management import CampaignManager, BulkOperationType, CampaignState
from database.models import CampaignStatus, TenantType


# Pydantic models for request/response validation

class CampaignCreateRequest(BaseModel):
    """Request model for creating a campaign."""
    name: str = Field(..., min_length=1, max_length=255, description="Campaign name")
    description: Optional[str] = Field(None, max_length=1000, description="Campaign description")
    tenant_id: str = Field(..., description="Tenant ID (academic or corporate)")
    template_id: str = Field(..., description="Template ID to use for this campaign")
    target_criteria: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Target criteria for contacts")
    contact_filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Contact filtering criteria")
    send_schedule: Optional[datetime] = Field(None, description="When to start sending emails")
    daily_send_limit: Optional[int] = Field(50, ge=1, le=1000, description="Daily email sending limit")
    time_between_emails: Optional[int] = Field(300, ge=1, description="Seconds between emails")
    enable_followups: Optional[bool] = Field(True, description="Enable follow-up emails")
    followup_delay_days: Optional[int] = Field(7, ge=1, le=30, description="Days to wait before follow-up")
    max_followups: Optional[int] = Field(2, ge=0, le=5, description="Maximum number of follow-ups")
    
    @validator('tenant_id')
    def validate_tenant_id(cls, v):
        if v not in [t.value for t in TenantType]:
            raise ValueError('Invalid tenant_id. Must be "academic" or "corporate"')
        return v


class CampaignUpdateRequest(BaseModel):
    """Request model for updating a campaign."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    target_criteria: Optional[Dict[str, Any]] = None
    contact_filters: Optional[Dict[str, Any]] = None
    send_schedule: Optional[datetime] = None
    daily_send_limit: Optional[int] = Field(None, ge=1, le=1000)
    time_between_emails: Optional[int] = Field(None, ge=1)
    enable_followups: Optional[bool] = None
    followup_delay_days: Optional[int] = Field(None, ge=1, le=30)
    max_followups: Optional[int] = Field(None, ge=0, le=5)


class CampaignCloneRequest(BaseModel):
    """Request model for cloning a campaign."""
    new_name: str = Field(..., min_length=1, max_length=255, description="Name for the cloned campaign")
    modifications: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Modifications to apply to the clone")


class BulkScheduleRequest(BaseModel):
    """Request model for bulk scheduling campaigns."""
    campaign_ids: List[str] = Field(..., min_items=1, description="List of campaign IDs to schedule")
    schedule_time: datetime = Field(..., description="When to schedule the campaigns")


class BulkOperationRequest(BaseModel):
    """Request model for bulk operations."""
    campaign_ids: List[str] = Field(..., min_items=1, description="List of campaign IDs")
    reason: Optional[str] = Field(None, max_length=255, description="Reason for the operation")


class CampaignResponse(BaseModel):
    """Response model for campaign data."""
    id: str
    name: str
    description: Optional[str]
    tenant_id: str
    status: str
    template_id: str
    target_criteria: Dict[str, Any]
    contact_filters: Dict[str, Any]
    send_schedule: Optional[datetime]
    daily_send_limit: int
    time_between_emails: int
    enable_followups: bool
    followup_delay_days: int
    max_followups: int
    total_contacts: int
    emails_sent: int
    emails_delivered: int
    emails_opened: int
    emails_clicked: int
    replies_received: int
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignListResponse(BaseModel):
    """Response model for campaign list with pagination."""
    campaigns: List[CampaignResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class BulkOperationResponse(BaseModel):
    """Response model for bulk operations."""
    operation_id: str
    operation_type: str
    success_count: int
    failure_count: int
    total_count: int
    errors: List[Dict[str, str]]
    completed_at: datetime


class CampaignHistoryItem(BaseModel):
    """Response model for campaign history items."""
    timestamp: datetime
    level: str
    message: str
    user_id: Optional[str]
    extra_data: Dict[str, Any]


class CampaignAnalyticsResponse(BaseModel):
    """Response model for campaign analytics."""
    campaign_id: str
    campaign_name: str
    current_status: str
    created_at: datetime
    statistics: Dict[str, Any]
    historical_analytics: List[Dict[str, Any]]


# Dependency functions

async def get_current_user_id() -> str:
    """Get current user ID (placeholder - implement with your auth system)."""
    # TODO: Implement actual user authentication
    # For now, return a mock user ID
    return "mock-user-id"


# Create router
router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])

# Initialize campaign manager
campaign_manager = CampaignManager()
logger = logging.getLogger(__name__)


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreateRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new campaign."""
    try:
        campaign = campaign_manager.create_campaign(
            user_id=user_id,
            campaign_data=campaign_data.dict(exclude_unset=True)
        )
        return CampaignResponse.from_orm(campaign)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get a campaign by ID."""
    try:
        campaign = campaign_manager.get_campaign(campaign_id, user_id)
        if not campaign:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        return CampaignResponse.from_orm(campaign)
    except Exception as e:
        logger.error(f"Error getting campaign {campaign_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/", response_model=CampaignListResponse)
async def get_campaigns(
    user_id: str = Depends(get_current_user_id),
    status_filter: Optional[str] = Query(None, description="Filter by campaign status"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    name_contains: Optional[str] = Query(None, description="Filter by name containing text"),
    created_after: Optional[datetime] = Query(None, description="Filter campaigns created after this date"),
    created_before: Optional[datetime] = Query(None, description="Filter campaigns created before this date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size")
):
    """Get campaigns with optional filtering and pagination."""
    try:
        filters = {}
        if status_filter:
            filters['status'] = status_filter
        if tenant_id:
            filters['tenant_id'] = tenant_id
        if name_contains:
            filters['name_contains'] = name_contains
        if created_after:
            filters['created_after'] = created_after
        if created_before:
            filters['created_before'] = created_before
        
        result = campaign_manager.get_campaigns(
            user_id=user_id,
            filters=filters,
            page=page,
            page_size=page_size
        )
        
        campaigns_response = [CampaignResponse.from_orm(c) for c in result['campaigns']]
        
        return CampaignListResponse(
            campaigns=campaigns_response,
            total_count=result['total_count'],
            page=result['page'],
            page_size=result['page_size'],
            total_pages=result['total_pages']
        )
    except Exception as e:
        logger.error(f"Error getting campaigns: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    updates: CampaignUpdateRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Update a campaign."""
    try:
        campaign = campaign_manager.update_campaign(
            campaign_id=campaign_id,
            user_id=user_id,
            updates=updates.dict(exclude_unset=True)
        )
        return CampaignResponse.from_orm(campaign)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating campaign {campaign_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a campaign."""
    try:
        success = campaign_manager.delete_campaign(campaign_id, user_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting campaign {campaign_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/{campaign_id}/clone", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def clone_campaign(
    campaign_id: str,
    clone_request: CampaignCloneRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Clone a campaign."""
    try:
        cloned_campaign = campaign_manager.clone_campaign(
            campaign_id=campaign_id,
            user_id=user_id,
            new_name=clone_request.new_name,
            modifications=clone_request.modifications
        )
        return CampaignResponse.from_orm(cloned_campaign)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error cloning campaign {campaign_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# State Management Endpoints

@router.post("/{campaign_id}/start", response_model=CampaignResponse)
async def start_campaign(
    campaign_id: str,
    send_immediately: bool = Query(False, description="Start sending immediately"),
    user_id: str = Depends(get_current_user_id)
):
    """Start a campaign."""
    try:
        campaign = campaign_manager.start_campaign(
            campaign_id=campaign_id,
            user_id=user_id,
            send_immediately=send_immediately
        )
        return CampaignResponse.from_orm(campaign)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting campaign {campaign_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(
    campaign_id: str,
    reason: Optional[str] = Query(None, description="Reason for pausing"),
    user_id: str = Depends(get_current_user_id)
):
    """Pause a campaign."""
    try:
        campaign = campaign_manager.pause_campaign(
            campaign_id=campaign_id,
            user_id=user_id,
            reason=reason
        )
        return CampaignResponse.from_orm(campaign)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error pausing campaign {campaign_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/{campaign_id}/resume", response_model=CampaignResponse)
async def resume_campaign(
    campaign_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Resume a paused campaign."""
    try:
        campaign = campaign_manager.resume_campaign(campaign_id=campaign_id, user_id=user_id)
        return CampaignResponse.from_orm(campaign)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error resuming campaign {campaign_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/{campaign_id}/cancel", response_model=CampaignResponse)
async def cancel_campaign(
    campaign_id: str,
    reason: Optional[str] = Query(None, description="Reason for cancelling"),
    user_id: str = Depends(get_current_user_id)
):
    """Cancel a campaign."""
    try:
        campaign = campaign_manager.cancel_campaign(
            campaign_id=campaign_id,
            user_id=user_id,
            reason=reason
        )
        return CampaignResponse.from_orm(campaign)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error cancelling campaign {campaign_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# Bulk Operations

@router.post("/bulk/send-now", response_model=BulkOperationResponse)
async def bulk_send_now(
    request: BulkOperationRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Send multiple campaigns immediately."""
    try:
        result = campaign_manager.bulk_send_now(
            campaign_ids=request.campaign_ids,
            user_id=user_id
        )
        return BulkOperationResponse(
            operation_id=result.operation_id,
            operation_type=BulkOperationType.SEND_NOW.value,
            success_count=result.success_count,
            failure_count=result.failure_count,
            total_count=result.total_count,
            errors=result.errors,
            completed_at=result.completed_at
        )
    except Exception as e:
        logger.error(f"Error in bulk send now: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/bulk/schedule", response_model=BulkOperationResponse)
async def bulk_schedule(
    request: BulkScheduleRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Schedule multiple campaigns."""
    try:
        result = campaign_manager.bulk_schedule(
            campaign_ids=request.campaign_ids,
            user_id=user_id,
            schedule_time=request.schedule_time
        )
        return BulkOperationResponse(
            operation_id=result.operation_id,
            operation_type=BulkOperationType.SCHEDULE.value,
            success_count=result.success_count,
            failure_count=result.failure_count,
            total_count=result.total_count,
            errors=result.errors,
            completed_at=result.completed_at
        )
    except Exception as e:
        logger.error(f"Error in bulk schedule: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/bulk/cancel", response_model=BulkOperationResponse)
async def bulk_cancel(
    request: BulkOperationRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Cancel multiple campaigns."""
    try:
        result = campaign_manager.bulk_cancel(
            campaign_ids=request.campaign_ids,
            user_id=user_id,
            reason=request.reason
        )
        return BulkOperationResponse(
            operation_id=result.operation_id,
            operation_type=BulkOperationType.CANCEL.value,
            success_count=result.success_count,
            failure_count=result.failure_count,
            total_count=result.total_count,
            errors=result.errors,
            completed_at=result.completed_at
        )
    except Exception as e:
        logger.error(f"Error in bulk cancel: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/bulk/pause", response_model=BulkOperationResponse)
async def bulk_pause(
    request: BulkOperationRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Pause multiple campaigns."""
    try:
        result = campaign_manager.bulk_pause(
            campaign_ids=request.campaign_ids,
            user_id=user_id,
            reason=request.reason
        )
        return BulkOperationResponse(
            operation_id=result.operation_id,
            operation_type=BulkOperationType.PAUSE.value,
            success_count=result.success_count,
            failure_count=result.failure_count,
            total_count=result.total_count,
            errors=result.errors,
            completed_at=result.completed_at
        )
    except Exception as e:
        logger.error(f"Error in bulk pause: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/bulk/resume", response_model=BulkOperationResponse)
async def bulk_resume(
    request: BulkOperationRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Resume multiple campaigns."""
    try:
        result = campaign_manager.bulk_resume(
            campaign_ids=request.campaign_ids,
            user_id=user_id
        )
        return BulkOperationResponse(
            operation_id=result.operation_id,
            operation_type=BulkOperationType.RESUME.value,
            success_count=result.success_count,
            failure_count=result.failure_count,
            total_count=result.total_count,
            errors=result.errors,
            completed_at=result.completed_at
        )
    except Exception as e:
        logger.error(f"Error in bulk resume: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# Analytics and History

@router.get("/{campaign_id}/history", response_model=List[CampaignHistoryItem])
async def get_campaign_history(
    campaign_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get campaign history and state transitions."""
    try:
        history = campaign_manager.get_campaign_history(campaign_id, user_id)
        return [CampaignHistoryItem(**item) for item in history]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting campaign history {campaign_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{campaign_id}/analytics", response_model=CampaignAnalyticsResponse)
async def get_campaign_analytics(
    campaign_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get detailed analytics for a campaign."""
    try:
        analytics = campaign_manager.get_campaign_analytics(campaign_id, user_id)
        return CampaignAnalyticsResponse(**analytics)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting campaign analytics {campaign_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# Utility endpoints

@router.get("/{campaign_id}/valid-transitions")
async def get_valid_transitions(
    campaign_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get valid state transitions for a campaign."""
    try:
        campaign = campaign_manager.get_campaign(campaign_id, user_id)
        if not campaign:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        
        current_state = CampaignState(campaign.status)
        valid_transitions = campaign_manager.state_machine.get_valid_transitions(current_state)
        
        return {
            "current_state": current_state.value,
            "valid_transitions": [state.value for state in valid_transitions]
        }
    except Exception as e:
        logger.error(f"Error getting valid transitions for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/stats/summary")
async def get_campaigns_summary(
    user_id: str = Depends(get_current_user_id)
):
    """Get summary statistics for all user campaigns."""
    try:
        # Get all campaigns for the user
        result = campaign_manager.get_campaigns(user_id=user_id, page_size=1000)  # Get all
        campaigns = result['campaigns']
        
        # Calculate summary statistics
        total_campaigns = len(campaigns)
        status_counts = {}
        tenant_counts = {}
        
        for campaign in campaigns:
            # Count by status
            status_counts[campaign.status] = status_counts.get(campaign.status, 0) + 1
            # Count by tenant
            tenant_counts[campaign.tenant_id] = tenant_counts.get(campaign.tenant_id, 0) + 1
        
        return {
            "total_campaigns": total_campaigns,
            "status_breakdown": status_counts,
            "tenant_breakdown": tenant_counts,
            "recent_campaigns": len([c for c in campaigns if (datetime.now(timezone.utc) - c.created_at).days <= 7])
        }
    except Exception as e:
        logger.error(f"Error getting campaigns summary: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
