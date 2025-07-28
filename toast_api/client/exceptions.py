"""
Custom exceptions for Toast API client.
"""


class ToastAPIError(Exception):
    """Base exception for Toast API errors."""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data


class AuthenticationError(ToastAPIError):
    """Raised when authentication fails."""
    pass


class APIRequestError(ToastAPIError):
    """Raised when API request fails."""
    pass


class APIConnectionError(ToastAPIError):
    """Raised when connection to API fails."""
    pass


class APITimeoutError(ToastAPIError):
    """Raised when API request times out."""
    pass


class RateLimitError(ToastAPIError):
    """Raised when API rate limit is exceeded."""
    pass


class ValidationError(ToastAPIError):
    """Raised when request validation fails."""
    pass


class NotFoundError(ToastAPIError):
    """Raised when requested resource is not found."""
    pass


class PermissionError(ToastAPIError):
    """Raised when user lacks permission for the operation."""
    pass


class CacheError(ToastAPIError):
    """Raised when cache operations fail."""
    pass


class ConfigurationError(ToastAPIError):
    """Raised when configuration is invalid."""
    pass


class DataParsingError(ToastAPIError):
    """Raised when data parsing fails."""
    pass


class ServiceUnavailableError(ToastAPIError):
    """Raised when the Toast API service is unavailable."""
    pass


class TokenExpiredError(AuthenticationError):
    """Raised when authentication token has expired."""
    pass


class InvalidTokenError(AuthenticationError):
    """Raised when authentication token is invalid."""
    pass
