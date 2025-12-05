"""
Base Tool Mixin
Contains shared utility methods used across all tool mixins.
"""
from typing import Optional, Dict, Any


class BaseToolsMixin:
    """
    Base mixin providing shared utility methods for all tool categories.
    Requires self.audit to be initialized by the main AgentTools class.
    """
    
    # ==================== Tool: Log Step ====================
    def log_step(
        self,
        step: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True
    ) -> Dict[str, Any]:
        """
        Tool: log_step
        Log a step in the audit trail for compliance tracking.
        
        This tool allows agents to explicitly record actions, decisions,
        and observations during the verification workflow.
        
        Args:
            step: Identifier for this step (e.g., "validation_check")
            action: Human-readable description of what happened
            details: Optional additional details to log
            success: Whether the step was successful
            
        Returns:
            Dictionary confirming the logged entry
        """
        entry = self.audit.log_step(
            step=step,
            action=action,
            tool="log_step",
            input_data=details or {},
            success=success
        )
        
        return {
            "logged": True,
            "step": step,
            "action": action,
            "timestamp": entry.timestamp.isoformat() if hasattr(entry, 'timestamp') else None
        }
