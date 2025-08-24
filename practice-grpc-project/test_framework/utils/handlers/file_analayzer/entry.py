from dataclasses import dataclass


@dataclass
class LogEntry:
    """Represents a parsed log entry."""
    timestamp: str
    component: str
    subcomponent: str
    pid: str
    thread_id: str
    level: str
    process_id: str
    process_name: str
    type: str
    message: str
    raw_line: str
    line_number: int

    def __str__(self):
        """String representation of the log entry."""
        return (f"{self.timestamp} {self.component} {self.subcomponent} "
                f"[{self.type}] - {self.message}")
