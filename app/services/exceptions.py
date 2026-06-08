"""Domain exceptions raised by the service layer.

These exceptions are intentionally HTTP-agnostic. The router layer
is responsible for mapping them to appropriate HTTP status codes.
"""


class ServiceError(Exception):
    """Base class for all domain exceptions."""


class NotFoundError(ServiceError):
    """Raised when a requested entity does not exist."""


class AlreadyExistsError(ServiceError):
    """Raised when a uniqueness constraint would be violated."""


class ClientNotFoundError(NotFoundError):
    """Raised when a Client lookup fails."""


class ClientEmailAlreadyExistsError(AlreadyExistsError):
    """Raised when trying to create or update a Client with a taken email."""

class PetNotFoundError(NotFoundError):
    """Raised when a Pet lookup fails."""


class OwnerNotFoundError(NotFoundError):
    """Raised when trying to create a Pet for a Client that doesn't exist."""