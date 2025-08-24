import re
from typing import List, Optional

from test_framework.utils.handlers.file_analayzer.entry import LogEntry
from test_framework.utils import get_logger


class LogParser:
    """Enhanced parser for log files with support for multiple log formats."""

    def __init__(self):
        """Initialize the parser with multiple format patterns."""
        self.logger = get_logger(__name__)

        # Primary pattern for actual format: "DD HH:MM:SS.mmm ..." or "YYYY-MM-DD HH:MM:SS.mmm ..."
        self.pattern = re.compile(
            # Use non-capturing group for timestamp alternatives to avoid extra groups
            r'(?:(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{3})|(\d{1,2}\s\d{2}:\d{2}:\d{2}\.\d{3}))\s+'
            r'(\w+\s*\w*)\s+'  # component
            r'(\w+\s*\w*)\s+'  # subcomponent
            r'(\d+)\s+'  # pid
            r'(0x[0-9a-f]+)\s+'  # thread_id
            r'(\d+)\s+'  # level
            r'(\d+)\s+'  # process_id
            r'([_-]?\w+)\s+'  # process_name
            r'(\w+):\s+'  # type
            r'(.*)'  # message
        )

    def parse_line(self, line: str, line_number: int = 0) -> Optional[LogEntry]:
        """
        Parse a single line of log text with support for multiple formats.

        :param line: The log line to parse
        :param line_number: Line number in the file (for reference)
        :return: LogEntry object if parsing succeeds, None otherwise
        """
        try:
            line = line.strip()

            # Try primary structured pattern first (actual format)
            match = self.pattern.match(line)
            if match:
                groups = match.groups()
                # First two groups are timestamp alternatives, take whichever matched
                timestamp = groups[0] or groups[1]
                component, subcomponent, pid, thread_id, level, \
                    process_id, process_name, type_value, message = groups[2:]

                return LogEntry(
                    timestamp=timestamp,
                    component=component,
                    subcomponent=subcomponent,
                    pid=pid,
                    thread_id=thread_id,
                    level=level,
                    process_id=process_id,
                    process_name=process_name,
                    type=type_value,
                    message=message,
                    raw_line=line,
                    line_number=line_number,
                )
            if line and not line.startswith("#"):
                self.logger.warning(f"Failed to parse line {line_number}: {line}")

                return LogEntry(
                    timestamp="",
                    component="Unstructured",
                    subcomponent="",
                    pid="",
                    thread_id="",
                    level="",
                    process_id="",
                    process_name="",
                    type='Raw',
                    message=line,
                    raw_line=line,
                    line_number=line_number
                )

            return None
        except Exception as e:
            self.logger.warning(f"Failed to parse line {line_number}: {str(e)}")
            return None

    def parse_file(self, file_path: str) -> List[LogEntry]:
        """
        Parse a log file.

        :param file_path: Path to the log file
        :return: List of LogEntry objects
        """
        self.logger.info(f"Parsing log file: {file_path}")
        entries = []

        try:
            for encodings in ['utf-8', 'utf-8-sig', 'latin-1']:
                try:
                    with open(file_path, 'r', encoding=encodings) as f:
                        file_content = f.readlines()
                    self.logger.debug(f"Successfully opened file with {encodings} encoding.")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                # Fallback with error handling
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    file_content = f.readlines()
                self.logger.debug("Successfully opened file with utf-8 encoding.")

            for i, line in enumerate(file_content, 1):
                if line.strip():
                    entry = self.parse_line(line, i)
                    if entry:
                            entries.append(entry)

            self.logger.info(f"Parsed {len(entries)} entries from {file_path}")
            return entries
        except Exception as e:
            self.logger.error(f"Failed to parse file {file_path}: {str(e)}")
            return []

