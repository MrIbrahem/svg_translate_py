"""Public API for the CopySvgTranslate package."""

from .extraction import extract
from .injection import inject, start_injects
from .workflows import svg_extract_and_inject, svg_extract_and_injects

__all__ = [
    "extract",
    "inject",
    "start_injects",
    "svg_extract_and_inject",
    "svg_extract_and_injects",
]
