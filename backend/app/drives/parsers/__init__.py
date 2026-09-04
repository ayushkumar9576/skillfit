"""
app/drives/parsers/__init__.py
--------------------------------
Normalisation and output-contract subsystem for Drive Ingestion (Phase 4.2).

Sub-modules:
    base.py               — abstract BaseNormalizer interface
    standard_normalizer.py — deterministic whitespace / encoding normaliser
    contract.py            — ParsedDriveContent: the Phase 4.2 → Phase 4.3 contract

Public API:
    from app.drives.parsers import get_normalizer
    from app.drives.parsers.contract import ParsedDriveContent
"""

from app.drives.parsers.base import BaseNormalizer, NormalizationResult
from app.drives.parsers.standard_normalizer import StandardNormalizer


def get_normalizer() -> BaseNormalizer:
    """
    Return the active normaliser.

    Today returns StandardNormalizer v1.0.
    Future versions may be selected based on env config or drive metadata.
    """
    return StandardNormalizer()
