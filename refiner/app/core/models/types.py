from typing import NamedTuple, Protocol, runtime_checkable

from lxml import etree


@runtime_checkable
class FileUpload(Protocol):
    """
    Protocol defining the interface for file uploads.

    This protocol allows us to work with different types of file uploads
    (FastAPI's UploadFile, S3 files, local files, etc.) in a consistent way.

    Any class that implements the async read() method with the correct
    signature will automatically be compatible with this protocol.

    Examples:
        # FastAPI's UploadFile automatically works because it has read()
        async def handle_upload(file: UploadFile):
            content = await file.read()

        # Custom S3 implementation
        class S3FileUpload:
            async def read(self) -> bytes:
                # S3 specific implementation
                return await s3.get_object(...)

        # Custom ZIP implementation
        class ZipFileUpload:
            async def read(self) -> bytes:
                # ZIP specific implementation
                return zip_content
    """

    async def read(self) -> bytes:
        """
        Read the entire contents of the file.

        Returns:
            bytes: The complete contents of the file.

        Note:
            This is just the interface definition.
            Actual implementation must be provided by classes
            that want to be compatible with this protocol.
        """

        ...


# xml document types
class XMLFiles(NamedTuple):
    """
    Container for eICR and RR XML documents.

    Note:
        parse_xml is imported inside methods to avoid circular imports:
        - types.py defines XMLFiles
        - file_io.py uses XMLFiles
        - XMLFiles methods use parse_xml from file_io.py
    """

    eicr: str
    rr: str

    def parse_eicr(self) -> etree._Element:
        """
        Parse eICR content into XML element tree.
        """

        from ...services.file_io import parse_xml

        return parse_xml(self.eicr)

    def parse_rr(self) -> etree._Element:
        """
        Parse RR content into XML element tree.
        """

        from ...services.file_io import parse_xml

        return parse_xml(self.rr)
