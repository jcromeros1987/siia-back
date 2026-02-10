from typing import Generic, TypeVar, Optional, Callable
from enum import Enum
from dataclasses import dataclass

T = TypeVar("T")
E = TypeVar("E")


class ErrorCode(Enum):
    """Standard error codes for the application."""

    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DUPLICATE_ENTRY = "DUPLICATE_ENTRY"
    DATABASE_ERROR = "DATABASE_ERROR"
    INVALID_INPUT = "INVALID_INPUT"


@dataclass
class Error:
    """Represents an error with code and message."""

    code: ErrorCode
    message: str
    details: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert error to dictionary representation."""
        result = {
            "code": self.code.value,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


class Result(Generic[T]):
    """
    Result pattern implementation for error handling.

    Represents either a success (Ok) or failure (Err) state.
    """

    def __init__(
        self,
        value: Optional[T] = None,
        error: Optional[Error] = None,
        is_success: bool = True,
    ):
        self._value = value
        self._error = error
        self._is_success = is_success

    @staticmethod
    def ok(value: T) -> "Result[T]":
        """Create a successful result."""
        return Result(value=value, is_success=True)

    @staticmethod
    def err(error: Error) -> "Result[T]":
        """Create a failed result."""
        return Result(error=error, is_success=False)

    @staticmethod
    def err_from(
        code: ErrorCode, message: str, details: Optional[dict] = None
    ) -> "Result[T]":
        """Create a failed result from code and message."""
        error = Error(code=code, message=message, details=details)
        return Result.err(error)

    def is_ok(self) -> bool:
        """Check if the result is successful."""
        return self._is_success

    def is_err(self) -> bool:
        """Check if the result is an error."""
        return not self._is_success

    def unwrap(self) -> T:
        """
        Get the value from a successful result.
        Raises ValueError if the result is an error.
        """
        if self.is_err():
            raise ValueError(f"Called unwrap on an Err result: {self._error.message}")
        return self._value

    def unwrap_or(self, default: T) -> T:
        """Get the value or return a default if the result is an error."""
        return self._value if self.is_ok() else default

    def unwrap_or_else(self, f: Callable[[Error], T]) -> T:
        """Get the value or apply a function to the error."""
        return self._value if self.is_ok() else f(self._error)

    def expect(self, message: str) -> T:
        """
        Get the value or raise an error with the provided message.
        """
        if self.is_err():
            raise ValueError(f"{message}: {self._error.message}")
        return self._value

    def map(self, f: Callable[[T], "Result[E]"]) -> "Result[E]":
        """Apply a function to the value if successful."""
        if self.is_err():
            return Result.err(self._error)
        return f(self._value)

    def map_value(self, f: Callable[[T], E]) -> "Result[E]":
        """Transform the value if successful, preserving the result type."""
        if self.is_err():
            return Result.err(self._error)
        return Result.ok(f(self._value))

    def flat_map(self, f: Callable[[T], "Result[E]"]) -> "Result[E]":
        """Alias for map - apply a function that returns a Result."""
        return self.map(f)

    def map_err(self, f: Callable[[Error], Error]) -> "Result[T]":
        """Transform the error if present."""
        if self.is_err():
            return Result.err(f(self._error))
        return self

    def and_then(self, f: Callable[[T], "Result[E]"]) -> "Result[E]":
        """Chain operations that return Results."""
        if self.is_err():
            return Result.err(self._error)
        return f(self._value)

    def or_else(self, f: Callable[[Error], "Result[T]"]) -> "Result[T]":
        """Try an alternative operation if this result is an error."""
        if self.is_ok():
            return self
        return f(self._error)

    def get_error(self) -> Optional[Error]:
        """Get the error from a failed result."""
        return self._error if self.is_err() else None

    def to_dict(self) -> dict:
        """Convert result to dictionary representation."""
        if self.is_ok():
            return {
                "success": True,
                "data": self._value,
            }
        else:
            return {
                "success": False,
                "error": self._error.to_dict(),
            }

    def __repr__(self) -> str:
        if self.is_ok():
            return f"Ok({self._value})"
        else:
            return f"Err({self._error})"
