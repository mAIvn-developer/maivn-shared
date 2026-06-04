"""Log writers for handling thread-safe console and file output.

File writes are enqueued and flushed by a single background worker thread so
high-concurrency async workloads avoid spawning per-log write tasks.
"""

# pyright: strict
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
        self._log_file: Path | None = log_file
        self._write_lock: threading.Lock = threading.Lock()
        self._file_logging_enabled: bool = log_file is not None
        self._queue_size: int = max(1, queue_size)

        self._file_queue: queue.Queue[str] | None = None
        self._worker_thread: threading.Thread | None = None
        self._shutdown_event: threading.Event = threading.Event()
        self._dropped_lines: int = 0

        if self._file_logging_enabled:
            self._file_queue = queue.Queue[str](maxsize=self._queue_size)
            self._worker_thread = threading.Thread(
                target=self._file_writer_loop,
                name="maivn-log-writer",
                daemon=True,
            )
            self._worker_thread.start()

    def __del__(self) -> None:  # pragma: no cover - best effort cleanup
        try:
            self.close()
        except Exception:  # noqa: BLE001 - logging cleanup must never raise in finalizers.
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
        """Flush queued file writes and stop the background writer thread.

        After the worker stops, file logging is marked disabled so any
        post-close write short-circuits deterministically instead of being
        silently enqueued into a queue no thread will ever drain.
        """
        worker_thread = self._worker_thread
        file_queue = self._file_queue
        if not self._file_logging_enabled or worker_thread is None or file_queue is None:
            return

        deadline = time.monotonic() + max(0.0, drain_timeout_seconds)
        while not file_queue.empty() and time.monotonic() < deadline:
            time.sleep(0.01)

        self._shutdown_event.set()
        worker_thread.join(timeout=max(0.1, drain_timeout_seconds))
        self._worker_thread = None
        self._file_logging_enabled = False

    # MARK: - Queue Handling

    def _enqueue_file_write(self, content: str) -> None:
        """Enqueue a file line, dropping oldest on sustained overload."""
        file_queue = self._file_queue
        if file_queue is None:
            self._write_to_file_sync(content)
            return

        try:
            file_queue.put_nowait(content)
            return
        except queue.Full:
            pass

        # Drop oldest line under pressure to preserve forward progress.
        try:
            _ = file_queue.get_nowait()
            file_queue.task_done()
            self._dropped_lines += 1
        except queue.Empty:
            self._dropped_lines += 1

        try:
            file_queue.put_nowait(content)
        except queue.Full:
            self._dropped_lines += 1
            return

        self._emit_drop_notice_if_needed()

    def _emit_drop_notice_if_needed(self) -> None:
        """Emit drop summary occasionally to avoid noisy stderr spam."""
        if self._dropped_lines == 0 or self._dropped_lines % 100 != 0:
            return
        # Last-resort stderr fallback must stay ASCII-only.
        print(
            f"[MaivnLogger] Dropped {self._dropped_lines} queued log lines due to backpressure",
            file=sys.stderr,
        )

    def _file_writer_loop(self) -> None:
        """Background worker loop for serial file writes."""
        file_queue = self._file_queue
        if file_queue is None:
            return

        while not self._shutdown_event.is_set() or not file_queue.empty():
            try:
                content = file_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            try:
                self._write_to_file_sync(content)
            finally:
                file_queue.task_done()

    # MARK: - Synchronous Write Operations

    def _write_to_console_sync(self, content: str) -> None:
        """Write to console synchronously."""
        with self._write_lock:
            StreamWriter.write_to_stream(sys.stdout, content)

    def _write_to_file_sync(self, content: str) -> None:
        """Write to file synchronously."""
        log_file = self._log_file
        if not self._file_logging_enabled or log_file is None:
            return

        with self._write_lock:
            try:
                with open(log_file, "a", encoding="utf-8") as file_handle:
                    StreamWriter.write_to_stream(file_handle, content)
            except Exception as exc:  # noqa: BLE001 - file logging must not crash callers.
                # Last-resort stderr fallback must stay ASCII-only.
                print(f"[MaivnLogger] Failed to write to file: {exc}", file=sys.stderr)
