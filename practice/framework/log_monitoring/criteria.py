#!/usr/bin/env python3
"""
Log Search Criteria - Simple data model for log searches

Supports all standard log levels: DEBUG, INFO, WARN, ERROR
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class LogCriteria:
    """Simple search criteria for log entries."""
    message_contains: str
    component: str = ""
    process_name: str = ""
    entry_type: str = ""  # Empty by default - matches any log level
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for internal use."""
        result = {"message_contains": self.message_contains}
        if self.component:
            result["component"] = self.component
        if self.process_name:
            result["process_name"] = self.process_name
        if self.entry_type:  # Only include if specifically set
            result["entry_type"] = self.entry_type
        return result

    # ========== SIMPLE HELPER METHODS ==========

    @classmethod
    def ui_switch_start(cls, expected_user: str) -> 'LogCriteria':
        """Common pattern: UI switch start event."""
        return cls("Switching to Login UI", "DesktopAgent", expected_user)

    @classmethod
    def ui_switch_end(cls) -> 'LogCriteria':
        """Common pattern: UI switch end event."""
        return cls("Opened proxcard screen", "LoginPlugin", "_securityagent")

    @classmethod
    def ui_timing_pair(cls, expected_user: str) -> tuple['LogCriteria', 'LogCriteria']:
        """Get both start and end criteria for common UI timing."""
        return (cls.ui_switch_start(expected_user), cls.ui_switch_end())

    @classmethod
    def card_to_proxcard_pair(cls) -> tuple['LogCriteria', 'LogCriteria']:
        """Get card detection to proxcard screen timing criteria."""
        card_detected = cls("Card detected on reader", "DeviceManager", "root")
        proxcard_end = cls("Opened proxcard screen", "LoginPlugin", "_securityagent")
        return (card_detected, proxcard_end)

    @classmethod
    def realtime_list(cls, *criteria: 'LogCriteria') -> list:
        """Convert multiple criteria to list of dicts for real-time monitoring."""
        return [c.to_dict() for c in criteria]