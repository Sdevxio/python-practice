from datetime import datetime
from typing import List, Tuple, Union

from test_framework.utils import get_logger
from test_framework.utils.handlers.file_analayzer.entry import LogEntry


class LogExtractor:
    """Extract and filter log data for test validation - focused on test needs, not regex complexity."""

    def __init__(self):
        """Initialize the extractor."""
        self.logger = get_logger(__name__)
        self._logged_timestamp_errors = set()  # Track already logged timestamp errors

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime object."""
        timestamp_format = [
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%d %H:%M:%S.%f",
            "%d %H:%M:%S"
        ]

        for fmt in timestamp_format:
            try:
                parsed_time = datetime.strptime(timestamp_str, fmt)
                # For day-only timestamps, assume 00:00:00
                if fmt.startswith("%d"):
                    current_time = datetime.now()
                    parsed_time = parsed_time.replace(
                        year=current_time.year,
                        month=current_time.month)
                return parsed_time
            except ValueError:
                continue

            # Log error only once if unique timestamp
        if timestamp_str not in self._logged_timestamp_errors:
            self.logger.error(f"Timestamp format not recognized: {timestamp_str}")
            self._logged_timestamp_errors.add(timestamp_str)
        return datetime.min

    def _matches_criteria(self, entry: LogEntry, **criteria) -> bool:
        """Check if entry matches field criteria."""
        for field_name, pattern in criteria.items():
            if not hasattr(entry, field_name):
                return False

            field_value = getattr(entry, field_name)
            field_str = str(field_value) if field_value is not None else ""
            pattern_str = str(pattern)

            if pattern_str not in field_str.lower():
                return False

        return True

    def find_entries_containing(self, entries: List[LogEntry], text: str,
                                field: str = "message") -> List[LogEntry]:
        """
        Find entries containing specific text.

        :param entries: List of log entries to search
        :param text: Text to search for
        :param field: Field to search in (default: "message")
        :return: List of matching entries

        Usage:
            # Find entries containing "admin"
            admin_entries = extractor.find_entries_containing(entries, "admin")

            # Find entries with "card" in message
            card_entries = extractor.find_entries_containing(entries, "card")

            # Find entries with "AuthService" in component field
            auth_entries = extractor.find_entries_containing(entries, "AuthService", "component")
        """
        results = []
        search_text = text.lower()

        for entry in entries:
            if hasattr(entry, field):
                field_value = str(getattr(entry, field)).lower()
                if search_text in field_value:
                    results.append(entry)

        self.logger.info(f"Found {len(results)} entries containing '{text}' in {field}")
        return results

    def find_user_activity(self, entries: List[LogEntry], username: str) -> List[LogEntry]:
        """
        Find all log entries related to a specific user.

        :param entries: List of log entries to search
        :param username: Username to search for
        :return: List of entries mentioning the user

        Usage:
            user_entries = extractor.find_user_activity(entries, "admin")
            user_entries = extractor.find_user_activity(entries, "john.doe")
        """
        return self.find_entries_containing(entries, username, "message")

    def find_card_activity(self, entries: List[LogEntry], card_id: str = None) -> List[LogEntry]:
        """
        Find all log entries related to card activity.

        :param entries: List of log entries to search
        :param card_id: Specific card ID to search for (optional)
        :return: List of card-related entries

        Usage:
            all_card_activity = extractor.find_card_activity(entries)
            specific_card = extractor.find_card_activity(entries, "A1B2C3D4")
        """
        if card_id:
            return self.find_entries_containing(entries, card_id, "message")
        else:
            return self.find_entries_containing(entries, "card", "message")


    def find_error_entries(self, entries: List[LogEntry]) -> List[LogEntry]:
        """
        Find error log entries.

        Usage:
            errors = extractor.find_error_entries(entries)
        """
        return self.find_entries_containing(entries, "error", "type")

    def filter_entries(self, entries: List[LogEntry], **criteria) -> List[LogEntry]:
        """
        Generic filter by any field criteria.

        Usage:
            filtered = extractor.filter_entries(entries, component="AuthService", type="Info")
        """
        results = [entry for entry in entries if self._matches_criteria(entry, **criteria)]
        self.logger.info(f"Filtered {len(results)} entries from {len(entries)} with criteria: {criteria}")
        return results

    def find_entries_in_time_range(self, entries: List[LogEntry],
                                   start_time: Union[str, datetime],
                                   end_time: Union[str, datetime],
                                   **criteria) -> List[LogEntry]:
        """
        Find entries within time range.

        Usage:
            test_window = extractor.find_entries_in_time_range(
                entries, test_start_time, test_end_time
            )
        """
        if isinstance(start_time, str):
            start_time = self._parse_timestamp(start_time)
        if isinstance(end_time, str):
            end_time = self._parse_timestamp(end_time)

        results = []
        for entry in entries:
            if entry.timestamp:  # Skip entries without timestamps
                entry_time = self._parse_timestamp(entry.timestamp)

                if start_time <= entry_time <= end_time:
                    if not criteria or self._matches_criteria(entry, **criteria):
                        results.append(entry)

        self.logger.info(f"Found {len(results)} entries in time range")
        return results

    def find_latest_entries(self, entries: List[LogEntry],
                                  test_time: Union[str, datetime],
                                  time_window_seconds: int = 30,
                                  **criteria) -> List[Tuple[LogEntry, float]]:
        """
        Find entries closest to test execution time.

        :param entries: List of log entries
        :param test_time: When the test was executed
        :param time_window_seconds: How many seconds around test time to look
        :param criteria: Optional filters (component="AuthService", etc.)
        :return: List of (entry, seconds_from_test_time) sorted by proximity

        Usage:
            # Find any entries near test time
            closest = extractor.find_closest_to_test_time(entries, test_execution_time)

            # Find AuthService entries near test time
            auth_closest = extractor.find_closest_to_test_time(
                entries, test_execution_time, component="AuthService"
            )

            # Find entries containing "admin" near test time
            admin_closest = extractor.find_closest_to_test_time(
                entries, test_execution_time, message="admin"
            )
        """
        if isinstance(test_time, str):
            if test_time.lower() == 'now':
                target_time = datetime.now()
            else:
                target_time = self._parse_timestamp(test_time)
        else:
            target_time = test_time

        results = []
        for entry in entries:
            if entry.timestamp:  # Skip entries without timestamps
                entry_time = self._parse_timestamp(entry.timestamp)
                time_diff = abs((entry_time - target_time).total_seconds())

                if time_diff <= time_window_seconds:
                    if not criteria or self._matches_criteria(entry, **criteria):
                        results.append((entry, time_diff))

        # Sort by time proximity (closest first)
        results.sort(key=lambda x: abs((x[0] - target_time).total_seconds()))

        self.logger.info(f"Found {len(results)} entries within {time_window_seconds}s of test time")
        return results

    def has_user_activity(self, entries: List[LogEntry], username: str) -> bool:
        """
        Check if user has any activity in the logs.

        Usage:
            assert extractor.has_user_activity(entries, "admin"), "No admin activity found"
        """
        return bool(self.find_user_activity(entries, username))

    def has_card_activity(self, entries: List[LogEntry], card_id: str = None) -> bool:
        """
        Check if there's card activity in the logs.

        Usage:
            assert extractor.has_card_activity(entries), "No card activity found"
            assert extractor.has_card_activity(entries, "A1B2C3D4"), "Card not used"
        """
        return bool(self.find_card_activity(entries, card_id))


    def has_errors(self, entries: List[LogEntry]) -> bool:
        """
        Check if there are any errors in the logs.

        Usage:
            assert not extractor.has_errors(entries), "Unexpected errors found"
        """
        return bool(self.find_error_entries(entries))

    def log_messages(self, entries: List[LogEntry], title: str = "Entries", limit: int = 5):
        """Simple logging for test visibility."""
        self.logger.info(f"=== {title} ({len(entries)} found) ===")
        for i, entry in enumerate(entries[:limit], 1):
            timestamp = entry.timestamp if entry.timestamp else "No timestamp"
            self.logger.info(f"{i:2d}: {timestamp} - {entry.message}")
        if len(entries) > limit:
            self.logger.info(f"... and {len(entries) - limit} more")

    def get_messages(self, entries: List[LogEntry]) -> List[str]:
        """Get messages for test assertions."""
        return [entry.message for entry in entries]

    def get_timestamps(self, entries: List[LogEntry]) -> List[str]:
        """Get timestamps for test assertions."""
        return [entry.timestamp for entry in entries]

    def find_latest_entry_with_criteria(self, entries: List[LogEntry],
                                        message_contains: str = None,
                                        component: str = None,
                                        entry_type: str = None,
                                        process_name: str = None) -> LogEntry:
        """
        Find the latest entry matching multiple criteria.

        :param entries: List of log entries to search
        :param message_contains: Text that must be in the message
        :param component: Component name to match
        :param entry_type: Entry type to match (Info, Debug, Error, etc.)
        :param process_name: Process name to match
        :return: Latest matching LogEntry or None if no match found

        Usage:
            latest = extractor.find_latest_entry_with_criteria(
                entries,
                message_contains="File system operations optimized",
                component="DesktopAgent",
                entry_type="Info",
                process_name="admin"
            )
        """
        # Build criteria
        criteria = {}
        if component:
            criteria["component"] = component
        if entry_type:
            criteria["type"] = entry_type
        if message_contains:
            criteria["message"] = message_contains
        if process_name:
            criteria["process_name"] = process_name

        # Filter by criteria first
        matching_entries = self.filter_entries(entries, **criteria)

        # Then filter by message if specified
        if message_contains:
            matching_entries = self.filter_entries(matching_entries, message=message_contains)

        if not matching_entries:
            return None

        # Find latest entry
        latest_entry = max(matching_entries,
                           key=lambda x: self._parse_timestamp(x.timestamp) if x.timestamp else datetime.min)

        self.logger.info(f"Found latest entry matching criteria: {latest_entry.timestamp} - {latest_entry.message}")
        return latest_entry


    def find_xml_entries(self, entries: List[LogEntry], expected_value: str = None) -> List[LogEntry]:

        xml_entries = self.find_entries_containing(entries, text=expected_value, field="message")
        for entry in xml_entries:
            if expected_value in entry.message:
                self.logger.info(f"Found XML entry: {entry.message}")
                return [entry]
        self.logger.info(f"XML entry not found: {expected_value}")
        return None

