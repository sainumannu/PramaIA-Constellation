"""
Central service for emitting events to the event bus.
All services should use this to emit events instead of calling the event endpoint directly.

This service handles:
- Event validation
- Centralized event emission to the trigger system
- Error handling and logging
"""

from typing import Dict, Any, Optional
from datetime import datetime
from backend.routers.event_trigger_system import EventPayload, EventMetadata, process_generic_event
from backend.utils import get_logger
from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
import asyncio

logger = get_logger(__name__)


async def emit_event(
    event_type: str,
    source: str,
    data: Dict[str, Any],
    user_id: Optional[str] = None,
    metadata_extra: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None
) -> bool:
    """
    Emit an event to the PramaIA event bus.
    
    This function constructs the event payload and sends it to the trigger system
    for processing. Events are matched against registered triggers and workflows
    are executed if conditions are met.
    
    Args:
        event_type: Type of event (must be registered in event source)
                   Example: "file_upload", "document_processed", "timer_tick"
        source: Source ID generating the event
               Example: "web-client-upload", "document-monitor", "scheduler"
        data: Event data (should match source schema)
             Example: {"filename": "doc.pdf", "file_size": 1024}
        user_id: Optional user ID associated with the event
        metadata_extra: Additional metadata to include
    
    Returns:
        True if event was processed successfully, False otherwise
    
    Example:
        >>> success = await emit_event(
        ...     event_type="file_upload",
        ...     source="web-client-upload",
        ...     data={"filename": "report.pdf", "file_size": 2048},
        ...     user_id="user-123"
        ... )
    """
    try:
        # Validate inputs
        if not event_type or not source:
            logger.error(
                "Invalid emit_event call: missing event_type or source",
                extra={"event_type": event_type, "source": source}
            )
            return False
        
        if not data or not isinstance(data, dict):
            logger.error(
                "Invalid emit_event call: data must be a non-empty dict",
                extra={"data_type": type(data).__name__}
            )
            return False
        
        # Build metadata
        metadata = EventMetadata(
            source=source,
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id,
            additional_data=metadata_extra or {}
        )
        
        # Build event payload
        payload = EventPayload(
            event_type=event_type,
            data=data,
            metadata=metadata
        )
        
        # Send to /api/events/process using internal call
        # This avoids network overhead and ensures reliable local processing
        db_session = db if db else SessionLocal()
        try:
            result = await process_generic_event(payload, db=db_session)
            
            # Log successful emission
            logger.info(
                f"Event emitted successfully: {event_type} from {source}",
                extra={
                    "event_type": event_type,
                    "source": source,
                    "user_id": user_id,
                    "triggers_matched": result.results.__len__() if hasattr(result, 'results') else 0
                }
            )
            
            return result.status == "processed"
        
        finally:
            if not db:  # Only close if we created the session
                db_session.close()
    
    except Exception as e:
        logger.error(
            f"Error emitting event {event_type} from {source}",
            exc_info=True,
            extra={
                "event_type": event_type,
                "source": source,
                "error": str(e)
            }
        )
        return False
