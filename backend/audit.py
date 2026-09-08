"""Helper pencatatan Audit Log untuk aktivitas admin/owner."""
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from models import AuditLog, User


def log_action(db: AsyncSession, actor: User, action: str, entity_type: str, description: str, *,
               entity_id: Optional[str] = None, entity_label: Optional[str] = None, meta: Optional[dict[str, Any]] = None) -> AuditLog:
    """Tambahkan entri audit ke session (commit dilakukan oleh pemanggil)."""
    entry = AuditLog(
        actor_id=actor.id, actor_username=actor.username, actor_role=actor.role, action=action, entity_type=entity_type,
        entity_id=entity_id, entity_label=entity_label, description=description, meta=meta,
    )
    db.add(entry)
    return entry
