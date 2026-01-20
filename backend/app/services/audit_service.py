"""Audit logging service."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog


async def log_action(
    db: AsyncSession,
    action: str,
    user_id: int = None,
    resource_type: str = None,
    resource_id: int = None,
    details: str = None,
    ip_address: str = None,
    user_agent: str = None,
    success: bool = True,
) -> AuditLog:
    """Log an action to the audit log."""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
        success=1 if success else 0,
    )
    db.add(audit_log)
    await db.commit()
    await db.refresh(audit_log)
    return audit_log
