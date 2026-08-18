from typing import Any, Protocol

from contracts.schemas.world import DocumentUnderstanding


class DocumentUnderstandingProvider(Protocol):
    """
    Interface for OCR and on-screen text extraction.
    """

    __version__: str = "1.0"

    def extract_text(self, media_path: str) -> list[DocumentUnderstanding]:
        """
        Extracts text, signs, or labels from the visual media.
        """
        ...

    def health(self) -> bool: ...

    def capabilities(self) -> dict[str, Any]: ...
