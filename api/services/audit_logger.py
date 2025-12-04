"""
Audit Logger Service
Tracks all agent actions for compliance and traceability.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from api.models.schemas import AuditLogEntry


class AuditLogger:
    """Service for logging all agent actions for audit trail."""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.logs_dir = self.data_dir / "audit_logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        self._current_session_id: Optional[str] = None
        self._session_logs: List[AuditLogEntry] = []
        self._step_counter: int = 0
    
    def start_session(self, session_id: str) -> None:
        """Start a new audit session."""
        self._current_session_id = session_id
        self._session_logs = []
        self._step_counter = 0
        
        self.log_step(
            step="session_start",
            action="Started new verification session",
            input_data={"session_id": session_id}
        )
    
    def log_step(
        self,
        step: str,
        action: str,
        agent: Optional[str] = None,
        tool: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLogEntry:
        """
        Log a single step in the workflow.
        
        Args:
            step: Step identifier (e.g., "extract_fields", "send_email")
            action: Human-readable description of the action
            agent: Which agent performed this action
            tool: Which tool was used
            input_data: Input parameters
            output_data: Output/result data
            success: Whether the step succeeded
            error_message: Error message if failed
            
        Returns:
            The created AuditLogEntry
        """
        self._step_counter += 1
        
        entry = AuditLogEntry(
            timestamp=datetime.utcnow(),
            step=f"{self._step_counter:03d}_{step}",
            action=action,
            agent=agent,
            tool=tool,
            input_data=self._sanitize_data(input_data),
            output_data=self._sanitize_data(output_data),
            success=success,
            error_message=error_message
        )
        
        self._session_logs.append(entry)
        
        # Also append to session file immediately for durability
        if self._current_session_id:
            self._append_to_file(entry)
        
        return entry
    
    def _sanitize_data(self, data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Remove sensitive data and truncate large values."""
        if data is None:
            return None
        
        sanitized = {}
        for key, value in data.items():
            # Skip sensitive fields
            if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'token', 'key']):
                sanitized[key] = "[REDACTED]"
            # Truncate long strings
            elif isinstance(value, str) and len(value) > 1000:
                sanitized[key] = value[:1000] + "... [truncated]"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _append_to_file(self, entry: AuditLogEntry) -> None:
        """Append log entry to session file."""
        if not self._current_session_id:
            return
        
        filepath = self.logs_dir / f"{self._current_session_id}.jsonl"
        
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry.model_dump(mode='json'), default=str) + "\n")
    
    def get_session_logs(self) -> List[AuditLogEntry]:
        """Get all logs from current session."""
        return self._session_logs.copy()
    
    def end_session(
        self,
        success: bool = True,
        final_result: Optional[Dict[str, Any]] = None
    ) -> List[AuditLogEntry]:
        """
        End the current session and return all logs.
        
        Args:
            success: Whether the overall session succeeded
            final_result: Final result summary
            
        Returns:
            List of all audit log entries
        """
        self.log_step(
            step="session_end",
            action="Completed verification session",
            output_data=final_result,
            success=success
        )
        
        logs = self._session_logs.copy()
        
        # Save complete session summary
        if self._current_session_id:
            self._save_session_summary(success, final_result)
        
        return logs
    
    def _save_session_summary(
        self,
        success: bool,
        final_result: Optional[Dict[str, Any]]
    ) -> None:
        """Save a summary of the session."""
        summary = {
            "session_id": self._current_session_id,
            "started_at": self._session_logs[0].timestamp.isoformat() if self._session_logs else None,
            "ended_at": datetime.utcnow().isoformat(),
            "total_steps": len(self._session_logs),
            "success": success,
            "final_result": final_result,
            "steps_summary": [
                {
                    "step": log.step,
                    "action": log.action,
                    "success": log.success
                }
                for log in self._session_logs
            ]
        }
        
        filepath = self.logs_dir / f"{self._current_session_id}_summary.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, default=str)
    
    def load_session_logs(self, session_id: str) -> List[AuditLogEntry]:
        """Load logs from a previous session."""
        filepath = self.logs_dir / f"{session_id}.jsonl"
        
        if not filepath.exists():
            return []
        
        logs = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    logs.append(AuditLogEntry(**data))
        
        return logs
    
    def list_sessions(self) -> List[dict]:
        """List all audit sessions."""
        sessions = []
        
        for filepath in self.logs_dir.glob("*_summary.json"):
            with open(filepath, 'r', encoding='utf-8') as f:
                summary = json.load(f)
                sessions.append(summary)
        
        return sorted(sessions, key=lambda x: x.get('ended_at', ''), reverse=True)
