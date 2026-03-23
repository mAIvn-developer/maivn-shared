"""Log writers for handling thread-safe console and file output.

File writes are enqueued and flushed by a single background worker thread so
high-concurrency async workloads avoid spawning per-log write tasks.
"""

from __future__ import annotations

import queue
import sys
import threading
import time
from pathlib import Path

from .config import DEFAULT_QUEUE_SIZE
from .formatters import StreamWriter


class LogWriter:
    """Handles log writes with non-blocking queued file persistence."""

    # MARK: - Initialization

    def __init__(
        self,
        log_file: Path | None = None,
        *,
        queue_size: int = DEFAULT_QUEUE_SIZE,
    ) -> None:
        """Initialize the log writer.

        Args:
            log_file: Path to log file (None disables file logging)
            queue_size: Max queued file lines before backpressure/drop policy
        """
        self._log_file = log_file
        self._write_lock = threading.Lock()
        self._file_logging_enabled = log_file is not None
        self._queue_size = max(1, queue_size)

        self._file_queue: queue.Queue[str] | None = None
        self._worker_thread: threading.Thread | None = None
        self._shutdown_event = threading.Event()
        self._dropped_lines = 0

        if self._file_logging_enabled:
            self._file_queue = queue.Queue(maxsize=self._queue_size)
            self._worker_thread = threading.Thread(
                target=self._file_writer_loop,
                name="maivn-log-writer",
                daemon=True,
            )
            self._worker_thread.start()

    def __del__(self) -> None:  # pragma: no cover - best effort cleanup
        try:
            self.close()
        except Exception:
            return

    # MARK: - Properties

    @property
    def file_logging_enabled(self) -> bool:
        """Check if file logging is enabled."""
        return self._file_logging_enabled

    @property
    def log_file(self) -> Path | None:
        """Get the log file path."""
        return self._log_file

    # MARK: - Public Write Methods

    def write_to_console(self, content: str) -> None:
        """Write content to console (stdout)."""
        self._write_to_console_sync(content)

    def write_to_file(self, content: str) -> None:
        """Queue content for file writing."""
        if not self._file_logging_enabled or not self._log_file:
            return
        if not content.strip():
            return

        self._enqueue_file_write(content)

    def write_dual(self, console_content: str, file_content: str, to_console: bool = True) -> None:
        """Write to both console and file outputs."""
        if to_console and console_content.strip():
            self._write_to_console_sync(console_content)

        if self._file_logging_enabled and self._log_file and file_content.strip():
            self._enqueue_file_write(file_content)

    def close(self, *, drain_timeout_seconds: float = 2.0) -> None:
        """Flush queued file writes and stop the background writer thread."""
        if not self._file_logging_enabled or not self._worker_thread or not self._file_queue:
            return

        deadline = time.monotonic() + max(0.0, drain_timeout_seconds)
        while not self._file_queue.empty() and time.monotonic() < deadline:
            time.sleep(0.01)

        self._shutdown_event.set()
        self._worker_thread.join(timeout=max(0.1, drain_timeout_seconds))
        self._worker_thread = None

    # MARK: - Queue Handling

    def _enqueue_file_write(self, content: str) -> None:
        """Enqueue a file line, dropping oldest on sustained overload."""
        if not self._file_queue:
            self._write_to_file_sync(content)
            return

        try:
            self._file_queue.put_nowait(content)
            return
        except queue.Full:
            pass

        # Drop oldest line under pressure to preserve forward progress.
        try:
            _ = self._file_queue.get_nowait()
            self._file_queue.task_done()
            self._dropped_lines += 1
        except queue.Empty:
            self._dropped_lines += 1

        try:
            self._file_queue.put_nowait(content)
        except queue.Full:
            self._dropped_lines += 1
            return

        self._emit_drop_notice_if_needed()

    def _emit_drop_notice_if_needed(self) -> None:
        """Emit drop summary occasionally to avoid noisy stderr spam."""
        if self._dropped_lines == 0 or self._dropped_lines % 100 != 0:
            return
        print(
            f"[MaivnLogger] Dropped {self._dropped_lines} queued log lines due to backpressure",
            file=sys.stderr,
        )

    def _file_writer_loop(self) -> None:
        """Background worker loop for serial file writes."""
        if not self._file_queue:
            return

        while not self._shutdown_event.is_set() or not self._file_queue.empty():
            try:
                content = self._file_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            try:
                self._write_to_file_sync(content)
            finally:
                self._file_queue.task_done()

    # MARK: - Synchronous Write Operations

    def _write_to_console_sync(self, content: str) -> None:
        """Write to console synchronously."""
        with self._write_lock:
            StreamWriter.write_to_stream(sys.stdout, content)

    def _write_to_file_sync(self, content: str) -> None:
        """Write to file synchronously."""
        if not self._file_logging_enabled or not self._log_file:
            return

        with self._write_lock:
            try:
                with open(self._log_file, "a", encoding="utf-8") as file_handle:
                    StreamWriter.write_to_stream(file_handle, content)
            except Exception as exc:
                print(f"[MaivnLogger] Failed to write to file: {exc}", file=sys.stderr)
