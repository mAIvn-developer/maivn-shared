# pyright: strict
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

from collections.abc import Mapping
from typing import TypeAlias, cast

from maivn_shared._redaction import redact_sensitive_data

# MARK: - Constants

_VALUE_TRUNCATE_LENGTH = 200
_PUBLIC_ERROR_MESSAGE = "An internal error occurred."

_RETRYABLE_EXCEPTION_NAMES = frozenset(
    {
        "ConnectionError",
        "TimeoutError",
        "ConcurrencyError",
        "TemporaryError",
    }
)


# MARK: - Types

ErrorContext: TypeAlias = dict[str, object]
ErrorPayload: TypeAlias = dict[str, object]


# MARK: - Context Helpers


def _copy_context(context: object | None) -> ErrorContext:
    """Copy a context-like object using the same dict constructor semantics."""
    return cast(ErrorContext, dict(cast(Mapping[object, object], context or {})))


def _pop_base_error_fields(kwargs: ErrorContext) -> tuple[str | None, Exception | None]:
    """Pop base MaivnError keyword fields from subclass kwargs."""
    error_code = cast(str | None, kwargs.pop("error_code", None))
    cause = cast(Exception | None, kwargs.pop("cause", None))
    return error_code, cause


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
        context: ErrorContext | None = None,
        cause: Exception | None = None,
        **kwargs: object,
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
        self.message: str = message
        self.error_code: str = error_code or self.__class__.__name__
        self.context: ErrorContext = self._merge_context(context, kwargs)
        self.cause: Exception | None = cause

        if cause is not None:
            self.__cause__: BaseException | None = cause

    @staticmethod
    def _merge_context(
        context: ErrorContext | None,
        kwargs: Mapping[str, object],
    ) -> ErrorContext:
        """Merge explicit context with kwargs."""
        merged = _copy_context(context)
        merged.update(kwargs)
        return merged

    def to_dict(self) -> ErrorPayload:
        """Convert exception to a structured internal dictionary.

        This preserves the raw exception message for internal diagnostics, but
        redacts sensitive context values and does not include raw cause text.
        Use ``to_public_dict`` for public API responses or client-visible
        errors.

        Returns:
            Dictionary with error_type, error_code, message, and optional
            redacted context and cause type fields.
        """
        result: ErrorPayload = {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
        }

        if self.context:
            result["context"] = cast(ErrorContext, redact_sensitive_data(self.context))

        if self.cause:
            result["cause"] = type(self.cause).__name__

        return result

    def to_public_dict(self, *, message: str = _PUBLIC_ERROR_MESSAGE) -> ErrorPayload:
        """Convert exception to a public-safe dictionary.

        The public representation intentionally excludes raw exception text,
        args, context, and causes because those fields often carry private
        request data or internal implementation details.
        """
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": message,
            "retryable": is_retryable(self),
        }

    def with_context(self, **additional_context: object) -> MaivnError:
        """Return a new exception with additional context.

        This does not modify the original exception.

        Args:
            **additional_context: Additional context to add

        Returns:
            New exception with merged context
        """
        return type(self)(
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
        actual: object = None,
        suggestion: str | None = None,
        **kwargs: object,
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
        error_code, cause = _pop_base_error_fields(kwargs)
        context = self._build_context(
            kwargs.pop("context", None),
            setting=setting,
            expected=expected,
            actual=str(actual) if actual is not None else None,
            suggestion=suggestion,
        )
        context.update(kwargs)
        super().__init__(message, error_code=error_code, context=context, cause=cause)

    @staticmethod
    def _build_context(
        base_context: object | None,
        **fields: object,
    ) -> ErrorContext:
        """Build context dict from base and optional fields."""
        context = _copy_context(base_context)
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
        value: object = None,
        rule: str | None = None,
        **kwargs: object,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error description
            field: Name of the field that failed validation
            value: Value that failed validation
            rule: Validation rule that was violated
            **kwargs: Additional context
        """
        error_code, cause = _pop_base_error_fields(kwargs)
        context = _copy_context(kwargs.pop("context", None))

        if field is not None:
            context["field"] = field
        if value is not None:
            context["value"] = str(value)[:_VALUE_TRUNCATE_LENGTH]
        if rule is not None:
            context["rule"] = rule

        context.update(kwargs)
        super().__init__(message, error_code=error_code, context=context, cause=cause)


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
        **kwargs: object,
    ) -> None:
        """Initialize serialization error.

        Args:
            message: Error description
            data_type: Type of data being serialized
            operation: Operation that failed ('serialize' or 'deserialize')
            **kwargs: Additional context
        """
        error_code, cause = _pop_base_error_fields(kwargs)
        context = _copy_context(kwargs.pop("context", None))

        if data_type is not None:
            context["data_type"] = data_type
        if operation is not None:
            context["operation"] = operation

        context.update(kwargs)
        super().__init__(message, error_code=error_code, context=context, cause=cause)


# MARK: - Utility Functions


def wrap_exception(
    original: Exception,
    wrapper_type: type[MaivnError] = MaivnError,
    message: str | None = None,
    **context: object,
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

    error_code, _ = _pop_base_error_fields(context)
    wrapped_context = _copy_context(context.pop("context", None))
    wrapped_context.update(context)

    return wrapper_type(
        message or str(original),
        error_code=error_code,
        context=wrapped_context,
        cause=original,
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
