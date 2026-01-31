"""Safety service - Report and block management"""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Report, ReportReason
from app.schemas.safety import (
    Report as ReportSchema,
    ReportReason as ReportReasonSchema,
)


class SafetyService:
    """Service for safety operations (reports and blocks)"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_report_reasons(self) -> List[ReportReason]:
        """
        Get all report reasons

        Returns:
            List of ReportReason models
        """
        result = await self.db.execute(
            select(ReportReason).order_by(ReportReason.sort_order)
        )
        return list(result.scalars().all())

    async def create_report(
        self,
        user_id: str,
        target_type: str,
        target_id: str,
        reason_id: str,
        detail: Optional[str] = None,
    ) -> Optional[Report]:
        """
        Create a new report

        Args:
            user_id: Reporter user ID
            target_type: Type of target (character, conversation_message, creator)
            target_id: Target ID
            reason_id: Report reason ID
            detail: Optional additional detail

        Returns:
            Created Report or None if reason not found
        """
        # Verify reason exists
        result = await self.db.execute(
            select(ReportReason).where(ReportReason.id == reason_id)
        )
        reason = result.scalar_one_or_none()
        if not reason:
            return None

        # Map schema target_type to model target_type
        model_target_type = target_type
        if target_type == "message":
            model_target_type = Report.TARGET_TYPE_MESSAGE

        # Create report
        report = Report(
            reporter_user_id=user_id,
            reason_id=reason_id,
            target_type=model_target_type,
            target_id=target_id,
            detail=detail,
            status=Report.STATUS_OPEN,
        )
        self.db.add(report)
        await self.db.flush()

        # Load the reason relationship
        await self.db.refresh(report, ["reason"])

        return report

    def report_to_schema(self, report: Report) -> ReportSchema:
        """Convert Report model to schema"""
        status_map = {
            Report.STATUS_OPEN: "open",
            Report.STATUS_IN_PROGRESS: "in_progress",
            Report.STATUS_RESOLVED: "resolved",
            Report.STATUS_REJECTED: "rejected",
        }

        return ReportSchema(
            id=report.id,
            target_type=report.target_type,
            target_id=report.target_id,
            reason=ReportReasonSchema(
                id=report.reason.id,
                code=report.reason.reason_code,
                name=report.reason.label,
            ),
            status=status_map.get(report.status, "open"),
            created_at=report.created_at,
        )

    def reason_to_schema(self, reason: ReportReason) -> ReportReasonSchema:
        """Convert ReportReason model to schema"""
        return ReportReasonSchema(
            id=reason.id,
            code=reason.reason_code,
            name=reason.label,
        )
