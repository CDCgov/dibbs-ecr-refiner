class BaseApplicationException(Exception):
    """
    Base exception for all application-specific exceptions.
    """

    def __init__(self, message: str, details: dict | None = None):
        """
        Initialize the base application exception.

        Args:
            message: The error message to be displayed.
            details: Optional dictionary containing additional error details.
        """

        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# data Validation Exceptions
class ValidationError(BaseApplicationException):
    """
    Base class for validation errors.
    """

    pass


class InputValidationError(ValidationError):
    """
    Raised when input data fails validation.
    """

    pass


class XMLValidationError(ValidationError):
    """
    Raised when XML data fails validation or parsing.
    """

    pass


class SectionValidationError(ValidationError):
    """
    Raised when ECR sections fail validation.
    """

    pass


class XMLParsingError(BaseApplicationException):
    """
    Raised when XML parsing or XPath evaluation fails.
    """

    pass


class ConditionCodeError(BaseApplicationException):
    """
    Raised when processing condition codes fails.
    """

    pass


class StructureValidationError(BaseApplicationException):
    """
    Raised when XML structure doesn't match expected format.
    """

    pass


class ConfigurationActivationConflictError(BaseApplicationException):
    """
    Raised when there's an attempt to make more than one configuration corresponding to a configuration active, which violates a table constraint.
    """

    pass


# processing Exceptions
class ProcessingError(BaseApplicationException):
    """
    Base class for processing errors.
    """

    pass


class FileProcessingError(ProcessingError):
    """
    Raised when file processing fails.
    """

    pass


class ZipValidationError(BaseApplicationException):
    """
    Raised when there are issues with ZIP file validation or processing.
    """

    pass


class XMLProcessingError(ProcessingError):
    """
    Raised when XML processing fails.
    """

    pass


# resource Exceptions
class ResourceError(BaseApplicationException):
    """
    Base class for resource-related errors.
    """

    pass


class ResourceNotFoundError(ResourceError):
    """
    Raised when a requested resource is not found.
    """

    pass


class ResourceAccessError(ResourceError):
    """
    Raised when access to a resource is denied or fails.
    """

    pass


# service-specific Exceptions
class ECRError(BaseApplicationException):
    """
    Base class for ECR-specific errors.
    """

    pass


class ECRRefinementError(ECRError):
    """
    Raised when ECR refinement fails.
    """

    pass


class ECRMappingError(ECRError):
    """
    Raised when mapping ECR data fails.
    """

    pass


# integration Exceptions
class IntegrationError(BaseApplicationException):
    """
    Base class for external integration errors.
    """

    pass


class ExternalServiceError(IntegrationError):
    """
    Raised when an external service call fails.
    """

    pass


class ConfigurationError(BaseApplicationException):
    """
    Raised when there's a configuration-related error.
    """

    pass


# database-specific exceptions
class DatabaseError(BaseApplicationException):
    """
    Base class for database-related errors.
    """

    pass


class DatabaseConnectionError(DatabaseError):
    """
    Raised when database connection fails.
    """

    pass


class DatabaseQueryError(DatabaseError):
    """
    Raised when database query execution fails.
    """

    pass


class DatabaseDataError(DatabaseError):
    """
    Raised when database data is invalid or corrupt.
    """

    pass
