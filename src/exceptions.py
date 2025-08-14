"""
Custom exceptions for the FPL Data Collector.
"""


class FPLException(Exception):
    """Base exception for FPL Data Collector."""
    pass


class APIError(FPLException):
    """Exception raised when there's an error with the FPL API."""
    pass


class RateLimitError(APIError):
    """Exception raised when the API rate limit is exceeded."""
    pass


class ValidationError(FPLException):
    """Exception raised when data validation fails."""
    pass


class DataProcessingError(FPLException):
    """Exception raised when there's an error processing data."""
    pass


class ConfigurationError(FPLException):
    """Exception raised when there's a configuration error."""
    pass


class StorageError(FPLException):
    """Exception raised when there's an error with data storage."""
    pass


class NetworkError(FPLException):
    """Exception raised when there's a network-related error."""
    pass


class TimeoutError(FPLException):
    """Exception raised when a request times out."""
    pass
