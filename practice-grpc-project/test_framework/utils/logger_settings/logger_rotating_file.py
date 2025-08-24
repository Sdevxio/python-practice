import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


class ArchivingRotatingFileHandler(RotatingFileHandler):
    """Rotating file handler that archives old log files.
    This handler rotates log files and moves the oldest log file to an archive directory.
    It is useful for keeping a history of log files while managing disk space.

    Attributes:
        filename (str): The name of the log file.
        max_bytes (int): The maximum size of the log file before rotation.
        backup_count (int): The number of backup files to keep.
        encoding (str): The encoding of the log file.
        delay (bool): If True, the file is opened only when the first log message is emitted.
        archive_dir (str): Directory where old log files are archived.
    """

    def __init__(self, filename: str, max_bytes: int = 0, backup_count: int = 0, encoding: str = None,
                 delay: bool = False, archive_dir: str = None):
        """
        Initialize the ArchiveRotatingFileHandler.
        """
        super().__init__(filename, maxBytes=max_bytes, backupCount=backup_count, encoding=encoding, delay=delay)
        self.archive_dir = archive_dir

    def doRollover(self):
        """
        Override to support archiving old log files.
        This method is called when the log file reaches its maximum size.
        It moves the oldest log file to the archive directory and creates a new log file.
        """
        if self.stream:
            self.stream.close()
            self.stream = None

        if self.backupCount > 0 and self.archive_dir:
            try:
                # Handle the oldest log by moving it to archive
                oldest_backup = self.rotation_filename(f"{self.baseFilename}.{self.backupCount}")
                if os.path.exists(oldest_backup):
                    archive_path = os.path.join(
                        self.archive_dir,
                        f"{os.path.basename(self.baseFilename)}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{self.backupCount}"
                    )
                    os.rename(oldest_backup, archive_path)

                # Rotate the rest normally
                for i in range(self.backupCount - 1, 0, -1):
                    source = self.rotation_filename(f"{self.baseFilename}.{i}")
                    target = self.rotation_filename(f"{self.baseFilename}.{i + 1}")

                    if os.path.exists(source):
                        if os.path.exists(target):
                            os.remove(target)
                        os.rename(source, target)

                # Handle the current log
                target = self.rotation_filename(f"{self.baseFilename}.1")
                if os.path.exists(target):
                    os.remove(target)

                self.rotate(self.baseFilename, target)
            except Exception as e:
                # Fallback to standard rotation if archiving fails
                import traceback
                print(f"Error during log archiving: {e}")
                traceback.print_exc()
                super().doRollover()
        else:
            # Use standard rotation if archiving not configured
            super().doRollover()

            # Reopen file
        self.mode = 'w'
        self.stream = self._open()