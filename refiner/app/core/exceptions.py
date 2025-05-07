class BaseApplicationException(Exception):
    """Base exception for all application-specific exceptions."""

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# data Validation Exceptions
class ValidationError(BaseApplicationException):
    """Base class for validation errors."""

    pass


class InputValidationError(ValidationError):
    """Raised when input data fails validation."""

    pass


class XMLValidationError(ValidationError):
    """Raised when XML data fails validation or parsing."""

    pass


class SectionValidationError(ValidationError):
    """Raised when ECR sections fail validation."""

    pass


# processing Exceptions
class ProcessingError(BaseApplicationException):
    """Base class for processing errors."""

    pass


class FileProcessingError(ProcessingError):
    """Raised when file processing fails."""

    pass


class ZipValidationError(BaseApplicationException):
    """Raised when there are issues with ZIP file validation or processing."""

    pass


class XMLProcessingError(ProcessingError):
    """Raised when XML processing fails."""

    pass


# resource Exceptions
class ResourceError(BaseApplicationException):
    """Base class for resource-related errors."""

    pass


class ResourceNotFoundError(ResourceError):
    """Raised when a requested resource is not found."""

    pass


class ResourceAccessError(ResourceError):
    """Raised when access to a resource is denied or fails."""

    pass


# service-specific Exceptions
class ECRError(BaseApplicationException):
    """Base class for ECR-specific errors."""

    pass


class ECRRefinementError(ECRError):
    """Raised when ECR refinement fails."""

    pass


class ECRMappingError(ECRError):
    """Raised when mapping ECR data fails."""

    pass


# integration Exceptions
class IntegrationError(BaseApplicationException):
    """Base class for external integration errors."""

    pass


class ExternalServiceError(IntegrationError):
    """Raised when an external service call fails."""

    pass


class ConfigurationError(BaseApplicationException):
    """Raised when there's a configuration-related error."""

    pass
