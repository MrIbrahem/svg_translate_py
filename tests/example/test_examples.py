"""Comprehensive tests for the CopySvgTranslate public API module (__init__.py)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from CopySvgTranslate import (
    extract,
    svg_extract_and_inject,
    inject,
)

FIXTURES_DIR = Path(__file__).parent


class TestIntegrationWorkflows:
    """Integration tests for high-level workflow functions."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.source_svg = FIXTURES_DIR / "source.svg"
        self.target_svg = self.test_dir / "before_translate.svg"
        self.output_svg = self.test_dir / "output.svg"
        self.data_file = self.test_dir / "data.json"

        # Copy target fixture
        self.target_svg.write_text(
            (FIXTURES_DIR / "before_translate.svg").read_text(encoding="utf-8"),
            encoding="utf-8"
        )

        # Run the workflow
        self.result = svg_extract_and_inject(
            self.source_svg,
            self.target_svg,
            output_file=self.output_svg,
            data_output_file=self.data_file,
            save_result=True,
        )

        expected_svg = FIXTURES_DIR / "after_translate.svg"
        self.expected_text = expected_svg.read_text(encoding="utf-8")

    def test_svg_extract_and_inject_end_to_end(self):
        """Test complete extract and inject workflow."""
        assert self.result is not None
        assert self.output_svg.exists()
        assert self.data_file.exists()

    def test_inject_with_dict(self):
        """Test inject with pre-extracted translations dict."""

        # Extract translations first
        translations = extract(FIXTURES_DIR / "source.svg")

        # Inject using the dict

        result, stats = inject(
            self.target_svg,
            output_dir=self.test_dir,
            all_mappings=translations,
            save_result=True,
            return_stats=True,
        )
        assert result is not None
        assert isinstance(stats, dict)
        assert "inserted_translations" in stats

        new_text = self.target_svg.read_text(encoding="utf-8")

        assert new_text == self.expected_text
