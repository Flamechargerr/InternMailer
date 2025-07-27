"""
Analytics Service - Comprehensive analytics and metrics with async support.

This module provides analytics data processing, metrics calculation, and
reporting functionality with both production and mock implementations.
"""

import asyncio
import random
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from .base import BaseService, ServiceConfig, with_error_handling, ServiceError


class MetricType(str, Enum):
    """Types of metrics."""
    EMAIL_SENT = "email_sent"
    EMAIL_DELIVERED = "email_delivered"
    EMAIL_OPENED = "email_opened"
    EMAIL_CLICKED = "email_clicked"
    EMAIL_REPLIED = "email_replied"
    EMAIL_BOUNCED = "email_bounced"
    CAMPAIGN_CREATED = "campaign_created"
    CONTACT_ADDED = "contact_added"


class TimeRange(str, Enum):
    """Time range for analytics."""
    LAST_24H = "24h"
    LAST_7D = "7d"
    LAST_30D = "30d"
    LAST_90D = "90d"
    LAST_YEAR = "1y"
    ALL_TIME = "all"


@dataclass
class MetricPoint:
    """A single metric data point."""
    timestamp: datetime
    metric_type: MetricType
    value: Union[int, float]
    campaign_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass 
class MetricsSummary:
    """Summary of metrics for a time period."""
    total_emails_sent: int = 0
    total_emails_delivered: int = 0
    total_emails_opened: int = 0
    total_emails_clicked: int = 0
    total_emails_replied: int = 0
    total_emails_bounced: int = 0
    
    # Calculated rates
    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    reply_rate: float = 0.0
    bounce_rate: float = 0.0
    
    # Campaigns
    total_campaigns: int = 0
    active_campaigns: int = 0
    
    # Contacts
    total_contacts: int = 0
    
    # Time period
    time_range: TimeRange = TimeRange.LAST_30D
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@dataclass
class CampaignMetrics:
    """Metrics for a specific campaign."""
    campaign_id: str
    campaign_name: Optional[str] = None
    emails_sent: int = 0
    emails_delivered: int = 0
    emails_opened: int = 0
    emails_clicked: int = 0
    emails_replied: int = 0
    emails_bounced: int = 0
    
    # Calculated rates
    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    reply_rate: float = 0.0
    bounce_rate: float = 0.0
    
    created_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None


@dataclass
class AnalyticsQuery:
    """Query parameters for analytics."""
    time_range: TimeRange = TimeRange.LAST_30D
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    campaign_ids: Optional[List[str]] = None
    user_ids: Optional[List[str]] = None
    metric_types: Optional[List[MetricType]] = None
    granularity: str = "day"  # hour, day, week, month
    include_metadata: bool = False


class AnalyticsService(BaseService):
    """Production analytics service."""
    
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self._batch_buffer = []
        self._flush_task = None
        
    async def _initialize_impl(self) -> None:
        """Initialize analytics service."""
        # Start background task for batching metrics
        self._flush_task = asyncio.create_task(self._flush_metrics_periodically())
        
    async def _cleanup_impl(self) -> None:
        """Cleanup analytics service resources."""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Flush any remaining metrics
        if self._batch_buffer:
            await self._flush_metrics()
    
    async def _health_check_impl(self) -> Dict[str, Any]:
        """Health check for analytics service."""
        return {
            "batch_buffer_size": len(self._batch_buffer),
            "batch_size_limit": self.config.analytics_batch_size,
            "flush_interval": self.config.analytics_flush_interval,
            "flush_task_running": self._flush_task and not self._flush_task.done()
        }
    
    @with_error_handling
    async def record_metric(self, metric: MetricPoint) -> None:
        """Record a single metric point."""
        async with self._ensure_initialized():
            self._batch_buffer.append(metric)
            
            # Flush immediately if buffer is full
            if len(self._batch_buffer) >= self.config.analytics_batch_size:
                await self._flush_metrics()
    
    @with_error_handling
    async def record_metrics_batch(self, metrics: List[MetricPoint]) -> None:
        """Record multiple metric points."""
        async with self._ensure_initialized():
            self._batch_buffer.extend(metrics)
            
            # Flush if buffer is getting large
            if len(self._batch_buffer) >= self.config.analytics_batch_size:
                await self._flush_metrics()
    
    @with_error_handling
    async def get_metrics_summary(self, query: Optional[AnalyticsQuery] = None) -> MetricsSummary:
        """Get metrics summary for a time period."""
        async with self._ensure_initialized():
            if query is None:
                query = AnalyticsQuery()
            
            # Calculate date range
            start_date, end_date = self._calculate_date_range(query)
            
            # In production, this would query the database
            # For now, return empty summary
            summary = MetricsSummary(
                time_range=query.time_range,
                start_date=start_date,
                end_date=end_date
            )
            
            return summary
    
    @with_error_handling
    async def get_campaign_metrics(self, campaign_id: str) -> Optional[CampaignMetrics]:
        """Get metrics for a specific campaign."""
        async with self._ensure_initialized():
            # In production, this would query the database
            return None
    
    @with_error_handling
    async def get_time_series_data(self, query: AnalyticsQuery) -> List[Dict[str, Any]]:
        """Get time series data for metrics."""
        async with self._ensure_initialized():
            start_date, end_date = self._calculate_date_range(query)
            
            # In production, this would generate time series data from database
            return []
    
    @with_error_handling
    async def get_top_campaigns(self, limit: int = 10, metric: str = "open_rate") -> List[CampaignMetrics]:
        """Get top performing campaigns."""
        async with self._ensure_initialized():
            # In production, this would query and rank campaigns
            return []
    
    def _calculate_date_range(self, query: AnalyticsQuery) -> tuple[datetime, datetime]:
        """Calculate start and end dates based on query."""
        end_date = query.end_date or datetime.now(timezone.utc)
        
        if query.start_date:
            start_date = query.start_date
        else:
            # Calculate based on time range
            if query.time_range == TimeRange.LAST_24H:
                start_date = end_date - timedelta(hours=24)
            elif query.time_range == TimeRange.LAST_7D:
                start_date = end_date - timedelta(days=7)
            elif query.time_range == TimeRange.LAST_30D:
                start_date = end_date - timedelta(days=30)
            elif query.time_range == TimeRange.LAST_90D:
                start_date = end_date - timedelta(days=90)
            elif query.time_range == TimeRange.LAST_YEAR:
                start_date = end_date - timedelta(days=365)
            else:  # ALL_TIME
                start_date = datetime(2020, 1, 1, tzinfo=timezone.utc)
        
        return start_date, end_date
    
    async def _flush_metrics(self):
        """Flush metrics batch to storage."""
        if not self._batch_buffer:
            return
        
        try:
            # In production, this would write to database
            metrics_to_flush = self._batch_buffer.copy()
            self._batch_buffer.clear()
            
            self.logger.info(
                "Flushed metrics batch",
                count=len(metrics_to_flush)
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to flush metrics batch",
                error=str(e),
                count=len(self._batch_buffer)
            )
            # In production, you might want to retry or save to a backup location
    
    async def _flush_metrics_periodically(self):
        """Background task to flush metrics periodically."""
        while True:
            try:
                await asyncio.sleep(self.config.analytics_flush_interval)
                await self._flush_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Error in periodic metrics flush", error=str(e))


class MockAnalyticsService(BaseService):
    """Mock analytics service for development and testing."""
    
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self._metrics_history = []
        self._campaigns_metrics = {}
        
    async def _initialize_impl(self) -> None:
        """Initialize mock analytics service."""
        await self._generate_sample_data()
        self.logger.info("Mock analytics service initialized with sample data")
    
    async def _cleanup_impl(self) -> None:
        """Cleanup mock analytics service."""
        self._metrics_history.clear()
        self._campaigns_metrics.clear()
    
    async def _health_check_impl(self) -> Dict[str, Any]:
        """Health check for mock analytics service."""
        return {
            "provider": "mock",
            "metrics_count": len(self._metrics_history),
            "campaigns_tracked": len(self._campaigns_metrics),
            "memory_usage_mb": len(str(self._metrics_history)) / 1024 / 1024
        }
    
    async def _generate_sample_data(self):
        """Generate sample analytics data."""
        now = datetime.now(timezone.utc)
        
        # Generate metrics for the last 30 days
        for days_ago in range(30):
            date = now - timedelta(days=days_ago)
            
            # Generate daily metrics
            daily_metrics = [
                MetricPoint(date, MetricType.EMAIL_SENT, random.randint(50, 200)),
                MetricPoint(date, MetricType.EMAIL_DELIVERED, random.randint(45, 190)),
                MetricPoint(date, MetricType.EMAIL_OPENED, random.randint(10, 60)),
                MetricPoint(date, MetricType.EMAIL_CLICKED, random.randint(2, 15)),
                MetricPoint(date, MetricType.EMAIL_REPLIED, random.randint(0, 5)),
                MetricPoint(date, MetricType.EMAIL_BOUNCED, random.randint(0, 10)),
            ]
            
            self._metrics_history.extend(daily_metrics)
        
        # Generate campaign metrics
        sample_campaigns = ["campaign_1", "campaign_2", "campaign_3"]
        for campaign_id in sample_campaigns:
            self._campaigns_metrics[campaign_id] = CampaignMetrics(
                campaign_id=campaign_id,
                campaign_name=f"Sample Campaign {campaign_id.split('_')[1]}",
                emails_sent=random.randint(100, 500),
                emails_delivered=random.randint(90, 480),
                emails_opened=random.randint(20, 120),
                emails_clicked=random.randint(5, 30),
                emails_replied=random.randint(1, 10),
                emails_bounced=random.randint(0, 20),
                created_at=now - timedelta(days=random.randint(1, 30))
            )
            
            # Calculate rates
            metrics = self._campaigns_metrics[campaign_id]
            if metrics.emails_sent > 0:
                metrics.delivery_rate = (metrics.emails_delivered / metrics.emails_sent) * 100
                metrics.bounce_rate = (metrics.emails_bounced / metrics.emails_sent) * 100
            
            if metrics.emails_delivered > 0:
                metrics.open_rate = (metrics.emails_opened / metrics.emails_delivered) * 100
                metrics.click_rate = (metrics.emails_clicked / metrics.emails_delivered) * 100
                metrics.reply_rate = (metrics.emails_replied / metrics.emails_delivered) * 100
    
    @with_error_handling
    async def record_metric(self, metric: MetricPoint) -> None:
        """Record a single metric point."""
        async with self._ensure_initialized():
            await asyncio.sleep(random.uniform(0.001, 0.005))  # Simulate processing
            self._metrics_history.append(metric)
            
            self.logger.info(
                "Mock metric recorded",
                metric_type=metric.metric_type.value,
                value=metric.value,
                campaign_id=metric.campaign_id
            )
    
    @with_error_handling
    async def record_metrics_batch(self, metrics: List[MetricPoint]) -> None:
        """Record multiple metric points."""
        async with self._ensure_initialized():
            await asyncio.sleep(random.uniform(0.01, 0.03))  # Simulate processing
            self._metrics_history.extend(metrics)
            
            self.logger.info("Mock metrics batch recorded", count=len(metrics))
    
    @with_error_handling
    async def get_metrics_summary(self, query: Optional[AnalyticsQuery] = None) -> MetricsSummary:
        """Get metrics summary for a time period."""
        async with self._ensure_initialized():
            await asyncio.sleep(random.uniform(0.02, 0.08))  # Simulate query processing
            
            if query is None:
                query = AnalyticsQuery()
            
            start_date, end_date = self._calculate_date_range(query)
            
            # Filter metrics by date range
            filtered_metrics = [
                m for m in self._metrics_history
                if start_date <= m.timestamp <= end_date
            ]
            
            # Aggregate metrics
            summary = MetricsSummary(
                time_range=query.time_range,
                start_date=start_date,
                end_date=end_date
            )
            
            for metric in filtered_metrics:
                if metric.metric_type == MetricType.EMAIL_SENT:
                    summary.total_emails_sent += int(metric.value)
                elif metric.metric_type == MetricType.EMAIL_DELIVERED:
                    summary.total_emails_delivered += int(metric.value)
                elif metric.metric_type == MetricType.EMAIL_OPENED:
                    summary.total_emails_opened += int(metric.value)
                elif metric.metric_type == MetricType.EMAIL_CLICKED:
                    summary.total_emails_clicked += int(metric.value)
                elif metric.metric_type == MetricType.EMAIL_REPLIED:
                    summary.total_emails_replied += int(metric.value)
                elif metric.metric_type == MetricType.EMAIL_BOUNCED:
                    summary.total_emails_bounced += int(metric.value)
            
            # Calculate rates
            if summary.total_emails_sent > 0:
                summary.delivery_rate = (summary.total_emails_delivered / summary.total_emails_sent) * 100
                summary.bounce_rate = (summary.total_emails_bounced / summary.total_emails_sent) * 100
            
            if summary.total_emails_delivered > 0:
                summary.open_rate = (summary.total_emails_opened / summary.total_emails_delivered) * 100
                summary.click_rate = (summary.total_emails_clicked / summary.total_emails_delivered) * 100
                summary.reply_rate = (summary.total_emails_replied / summary.total_emails_delivered) * 100
            
            # Mock campaign and contact counts
            summary.total_campaigns = len(self._campaigns_metrics)
            summary.active_campaigns = len([c for c in self._campaigns_metrics.values() if c.emails_sent > 0])
            summary.total_contacts = random.randint(100, 1000)
            
            return summary
    
    @with_error_handling
    async def get_campaign_metrics(self, campaign_id: str) -> Optional[CampaignMetrics]:
        """Get metrics for a specific campaign."""
        async with self._ensure_initialized():
            await asyncio.sleep(random.uniform(0.01, 0.03))
            return self._campaigns_metrics.get(campaign_id)
    
    @with_error_handling
    async def get_time_series_data(self, query: AnalyticsQuery) -> List[Dict[str, Any]]:
        """Get time series data for metrics."""
        async with self._ensure_initialized():
            await asyncio.sleep(random.uniform(0.03, 0.1))
            
            start_date, end_date = self._calculate_date_range(query)
            
            # Generate time series data points
            time_series = []
            current_date = start_date
            
            while current_date <= end_date:
                # Aggregate metrics for this time period
                period_metrics = [
                    m for m in self._metrics_history
                    if current_date <= m.timestamp < current_date + timedelta(days=1)
                ]
                
                data_point = {
                    "timestamp": current_date.isoformat(),
                    "emails_sent": sum(m.value for m in period_metrics if m.metric_type == MetricType.EMAIL_SENT),
                    "emails_delivered": sum(m.value for m in period_metrics if m.metric_type == MetricType.EMAIL_DELIVERED),
                    "emails_opened": sum(m.value for m in period_metrics if m.metric_type == MetricType.EMAIL_OPENED),
                    "emails_clicked": sum(m.value for m in period_metrics if m.metric_type == MetricType.EMAIL_CLICKED),
                }
                
                time_series.append(data_point)
                current_date += timedelta(days=1)
            
            return time_series
    
    @with_error_handling
    async def get_top_campaigns(self, limit: int = 10, metric: str = "open_rate") -> List[CampaignMetrics]:
        """Get top performing campaigns."""
        async with self._ensure_initialized():
            await asyncio.sleep(random.uniform(0.02, 0.05))
            
            campaigns = list(self._campaigns_metrics.values())
            
            # Sort by the specified metric
            if metric == "open_rate":
                campaigns.sort(key=lambda c: c.open_rate, reverse=True)
            elif metric == "click_rate":
                campaigns.sort(key=lambda c: c.click_rate, reverse=True)
            elif metric == "reply_rate":
                campaigns.sort(key=lambda c: c.reply_rate, reverse=True)
            elif metric == "delivery_rate":
                campaigns.sort(key=lambda c: c.delivery_rate, reverse=True)
            else:
                campaigns.sort(key=lambda c: c.emails_sent, reverse=True)
            
            return campaigns[:limit]
    
    def _calculate_date_range(self, query: AnalyticsQuery) -> tuple[datetime, datetime]:
        """Calculate start and end dates based on query."""
        end_date = query.end_date or datetime.now(timezone.utc)
        
        if query.start_date:
            start_date = query.start_date
        else:
            # Calculate based on time range
            if query.time_range == TimeRange.LAST_24H:
                start_date = end_date - timedelta(hours=24)
            elif query.time_range == TimeRange.LAST_7D:
                start_date = end_date - timedelta(days=7)
            elif query.time_range == TimeRange.LAST_30D:
                start_date = end_date - timedelta(days=30)
            elif query.time_range == TimeRange.LAST_90D:
                start_date = end_date - timedelta(days=90)
            elif query.time_range == TimeRange.LAST_YEAR:
                start_date = end_date - timedelta(days=365)
            else:  # ALL_TIME
                start_date = datetime(2020, 1, 1, tzinfo=timezone.utc)
        
        return start_date, end_date
    
    def get_all_metrics(self) -> List[MetricPoint]:
        """Get all recorded metrics for inspection (mock only)."""
        return self._metrics_history.copy()
    
    def get_campaign_data(self) -> Dict[str, CampaignMetrics]:
        """Get all campaign metrics for inspection (mock only)."""
        return self._campaigns_metrics.copy()
    
    def clear_all_data(self):
        """Clear all analytics data (mock only)."""
        self._metrics_history.clear()
        self._campaigns_metrics.clear()
