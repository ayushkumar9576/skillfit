"""
app/drives/extractors/__init__.py
-----------------------------------
Extraction subsystem for Drive Ingestion (Phase 4.2).

Extractors are responsible for:
    - Reading raw bytes from a source (PDF, text)
    - Producing a single string of extracted text
    - Reporting extraction metadata (method, version, warnings)

Extractors are NOT responsible for:
    - Normalisation
    - Intelligence generation
    - Database operations
    - HTTP concerns

Public API:
    from app.drives.extractors import get_extractor
    from app.drives.extractors.base import ExtractionResult
"""

from app.drives.extractors.base import BaseExtractor, ExtractionResult
from app.drives.extractors.pdf_extractor import PDFExtractor
from app.drives.extractors.text_extractor import TextExtractor
from app.core.enums import DriveSourceFormat


def get_extractor(source_format: DriveSourceFormat) -> BaseExtractor:
    """
    Return the appropriate extractor for the given source format.

    Args:
        source_format: DriveSourceFormat enum value.

    Returns:
        A BaseExtractor implementation.

    Raises:
        ValueError: if no extractor is registered for the format.
    """
    registry: dict[DriveSourceFormat, BaseExtractor] = {
        DriveSourceFormat.pdf:  PDFExtractor(),
        DriveSourceFormat.text: TextExtractor(),
    }
    extractor = registry.get(source_format)
    if extractor is None:
        raise ValueError(
            f"No extractor registered for source format: {source_format!r}. "
            f"Supported formats: {list(registry.keys())}"
        )
    return extractor
