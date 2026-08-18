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



class InputValidationError(ValidationError):
    """
    Raised when input data fails validation.
    """



class XMLValidationError(ValidationError):
    """
    Raised when XML data fails validation or parsing.
    """



class SectionValidationError(ValidationError):
    """
    Raised when ECR sections fail validation.
    """



class XMLParsingError(BaseApplicationException):
    """
    Raised when XML parsing or XPath evaluation fails.
    """



class ConditionCodeError(BaseApplicationException):
    """
    Raised when processing condition codes fails.
    """



class StructureValidationError(BaseApplicationException):
    """
    Raised when XML structure doesn't match expected format.
    """



# processing Exceptions
class ProcessingError(BaseApplicationException):
    """
    Base class for processing errors.
    """



class FileProcessingError(ProcessingError):
    """
    Raised when file processing fails.
    """



class ZipValidationError(BaseApplicationException):
    """
    Raised when there are issues with ZIP file validation or processing.
    """



class ZipSizeError(BaseApplicationException):
    """
    Raised when the uploaded ZIP is too big for processing.
    """



class XMLProcessingError(ProcessingError):
    """
    Raised when XML processing fails.
    """



# resource Exceptions
class ResourceError(BaseApplicationException):
    """
    Base class for resource-related errors.
    """



class ResourceNotFoundError(ResourceError):
    """
    Raised when a requested resource is not found.
    """



class ResourceAccessError(ResourceError):
    """
    Raised when access to a resource is denied or fails.
    """



# service-specific Exceptions
class ECRError(BaseApplicationException):
    """
    Base class for ECR-specific errors.
    """



class ECRRefinementError(ECRError):
    """
    Raised when ECR refinement fails.
    """



class ECRMappingError(ECRError):
    """
    Raised when mapping ECR data fails.
    """



# integration Exceptions
class IntegrationError(BaseApplicationException):
    """
    Base class for external integration errors.
    """



class ExternalServiceError(IntegrationError):
    """
    Raised when an external service call fails.
    """



class ConfigurationError(BaseApplicationException):
    """
    Raised when there's a configuration-related error.
    """



# database-specific exceptions
class DatabaseError(BaseApplicationException):
    """
    Base class for database-related errors.
    """



class DatabaseConnectionError(DatabaseError):
    """
    Raised when database connection fails.
    """



class DatabaseQueryError(DatabaseError):
    """
    Raised when database query execution fails.
    """



class DatabaseDataError(DatabaseError):
    """
    Raised when database data is invalid or corrupt.
    """



class RefinementException(Exception):
    """
    Exception raised during a failed refinement run.
    """

    def __init__(self, message: str, detail: str):
        """
        RefinementException constructor.

        Args:
            message (str): High-level error message
            detail (str): Additional detail describing the issue encountered
        """
        super().__init__(message)
        self.detail = detail
