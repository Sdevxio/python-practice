"""
Simple Log Monitoring - Consolidated single-purpose module

Combines all log monitoring functionality into a clean, minimal interface.
Eliminates duplication between file_analayzer and monitoring packages.

Public API:
- LogMonitor: Simple interface for all log monitoring needs
- LogCriteria: Search criteria data class
"""

from .criteria import LogCriteria
from .hybrid_monitor import HybridLogMonitor, create_hybrid_monitor

__all__ = ['LogCriteria', 'HybridLogMonitor', 'create_hybrid_monitor']