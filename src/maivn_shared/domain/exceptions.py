"""Shared exception hierarchy for Maivn packages.

This module defines a base exception class and common exception types
that are shared across maivn, maivn-server, and maivn-agents.

Design Principles:
- Rich context support for debugging
- Structured error output (to_dict)
- Extensible hierarchy for package-specific exceptions
- Consistent error codes across packages
"""

from __future__ import annotations

from typing import Any

# MARK: - Constants

_VALUE_TRUNCATE_LENGTH = 200

_RETRYABLE_EXCEPTION_NAMES = frozenset(
    {
        "ConnectionError",
        "TimeoutError",
        "ConcurrencyError",
        "TemporaryError",
    }
)

# MARK: - Base Exception


class MaivnError(Exception):
    """Base exception for all Maivn packages.

    Provides:
    - Structured context storage for debugging
    - Error codes for programmatic handling
    - Serialization to dict for API responses/logging
    - Cause chaining for exception wrapping

    All Maivn-specific exceptions should inherit from this class.
    """

    def __init__(
        self,
        message: str,
        *,
        error_code: str | None = None,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize exception with structured error information.

        Args:
            message: Human-readable error description
            error_code: Machine-readable error identifier (defaults to class name)
            context: Additional context data for debugging
            cause: Original exception that caused this error
            **kwargs: Additional context merged into context dict
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = self._merge_context(context, kwargs)
        self.cause = cause

        if cause is not None:
            self.__cause__ = cause

    @staticmethod
    def _merge_context(
        context: dict[str, Any] | None,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge explicit context with kwargs."""
        merged: dict[str, Any] = dict(context or {})
        merged.update(kwargs)
        return merged

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to structured dictionary.

        Useful for API responses, logging, and debugging.

        Returns:
            Dictionary with error_type, error_code, message, and optional
            context and cause fields.
        """
        result: dict[str, Any] = {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
        }

        if self.context:
            result["context"] = self.context

        if self.cause:
            result["cause"] = str(self.cause)

        return result

    def with_context(self, **additional_context: Any) -> MaivnError:
        """Return a new exception with additional context.

        This does not modify the original exception.

        Args:
            **additional_context: Additional context to add

        Returns:
            New exception with merged context
        """
        return self.__class__(
            self.message,
            error_code=self.error_code,
            context={**self.context, **additional_context},
            cause=self.cause,
        )


# MARK: - Configuration Errors


class ConfigurationError(MaivnError):
    """Raised when configuration is invalid or missing.

    Use for:
    - Missing required settings
    - Invalid setting values
    - Type mismatches in configuration
    """

    def __init__(
        self,
        message: str,
        *,
        setting: str | None = None,
        expected: str | None = None,
        actual: Any = None,
        suggestion: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize configuration error.

        Args:
            message: Error description
            setting: Name of the problematic setting
            expected: Expected type or value description
            actual: Actual value that caused the error
            suggestion: Suggestion for fixing the issue
            **kwargs: Additional context
        """
        context = self._build_context(
            kwargs.pop("context", None),
            setting=setting,
            expected=expected,
            actual=str(actual) if actual is not None else None,
            suggestion=suggestion,
        )
        super().__init__(message, context=context, **kwargs)

    @staticmethod
    def _build_context(
        base_context: dict[str, Any] | None,
        **fields: Any,
    ) -> dict[str, Any]:
        """Build context dict from base and optional fields."""
        context = dict(base_context or {})
        for key, value in fields.items():
            if value is not None:
                context[key] = value
        return context


# MARK: - Validation Errors


class ValidationError(MaivnError):
    """Raised when data validation fails.

    Use for:
    - Invalid input data
    - Schema validation failures
    - Constraint violations
    """

    def __init__(
        self,
        message: str,
        *,
        field: str | None = None,
        value: Any = None,
        rule: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error description
            field: Name of the field that failed validation
            value: Value that failed validation
            rule: Validation rule that was violated
            **kwargs: Additional context
        """
        context = dict(kwargs.pop("context", None) or {})

        if field is not None:
            context["field"] = field
        if value is not None:
            context["value"] = str(value)[:_VALUE_TRUNCATE_LENGTH]
        if rule is not None:
            context["rule"] = rule

        super().__init__(message, context=context, **kwargs)


# MARK: - Serialization Errors


class SerializationError(MaivnError):
    """Raised when serialization or deserialization fails.

    Use for:
    - JSON encoding/decoding failures
    - Pydantic model parsing failures
    - Data format conversion errors
    """

    def __init__(
        self,
        message: str,
        *,
        data_type: str | None = None,
        operation: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize serialization error.

        Args:
            message: Error description
            data_type: Type of data being serialized
            operation: Operation that failed ('serialize' or 'deserialize')
            **kwargs: Additional context
        """
        context = dict(kwargs.pop("context", None) or {})

        if data_type is not None:
            context["data_type"] = data_type
        if operation is not None:
            context["operation"] = operation

        super().__init__(message, context=context, **kwargs)


# MARK: - Utility Functions


def wrap_exception(
    original: Exception,
    wrapper_type: type[MaivnError] = MaivnError,
    message: str | None = None,
    **context: Any,
) -> MaivnError:
    """Wrap a generic exception in a MaivnError.

    If the exception is already a MaivnError, returns it unchanged
    (or with additional context if provided).

    Args:
        original: The exception to wrap
        wrapper_type: MaivnError subclass to wrap with
        message: Custom message (defaults to original message)
        **context: Additional context for the wrapped exception

    Returns:
        Wrapped MaivnError with original as cause
    """
    if isinstance(original, MaivnError):
        return original.with_context(**context) if context else original

    return wrapper_type(
        message or str(original),
        cause=original,
        **context,
    )


def is_retryable(exception: Exception) -> bool:
    """Check if an exception represents a retryable error.

    Retryable errors are typically transient issues that may
    succeed on retry (network issues, temporary service outages).

    Args:
        exception: Exception to check

    Returns:
        True if the error might succeed on retry
    """
    if isinstance(exception, (ConfigurationError, ValidationError)):
        return False

    return type(exception).__name__ in _RETRYABLE_EXCEPTION_NAMES


# MARK: - Exports

__all__ = [
    # Base
    "MaivnError",
    # Common errors
    "ConfigurationError",
    "ValidationError",
    "SerializationError",
    # Utilities
    "wrap_exception",
    "is_retryable",
]
