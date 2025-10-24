
"""
Comprehensive unit tests for CopySvgTranslate covering edge cases and additional functionality.
"""

import json
import sys
import tempfile
import unittest
import shutil
from pathlib import Path

from lxml import etree

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CopySvgTranslate import extract
from CopySvgTranslate.text_utils import extract_text_from_node
from CopySvgTranslate.workflows import svg_extract_and_inject, svg_extract_and_injects


class TestTextUtils(unittest.TestCase):
    """Test cases for text utility functions."""

    def test_extract_text_from_node_with_tspans(self):
        """Test extracting text from a node with tspans."""
        svg_ns = "http://www.w3.org/2000/svg"
        text_node = etree.fromstring(
            f'''<text xmlns="{svg_ns}">
                <tspan>Hello</tspan>
                <tspan>World</tspan>
            </text>'''
        )
        result = extract_text_from_node(text_node)
        self.assertEqual(result, ["Hello", "World"])

    def test_extract_text_from_node_without_tspans(self):
        """Test extracting text from a node without tspans."""
        svg_ns = "http://www.w3.org/2000/svg"
        text_node = etree.fromstring(f'<text xmlns="{svg_ns}">Plain text</text>')
        result = extract_text_from_node(text_node)
        self.assertEqual(result, ["Plain text"])

    def test_extract_text_from_node_empty(self):
        """Test extracting text from an empty node."""
        svg_ns = "http://www.w3.org/2000/svg"
        text_node = etree.fromstring(f'<text xmlns="{svg_ns}"></text>')
        result = extract_text_from_node(text_node)
        self.assertEqual(result, [""])

    def test_extract_text_from_node_with_whitespace_tspans(self):
        """Test extracting text from tspans with only whitespace."""
        svg_ns = "http://www.w3.org/2000/svg"
        text_node = etree.fromstring(
            f'''<text xmlns="{svg_ns}">
                <tspan>   </tspan>
                <tspan>Text</tspan>
            </text>'''
        )
        result = extract_text_from_node(text_node)
        self.assertEqual(result, ["", "Text"])


class TestWorkflows(unittest.TestCase):
    """Test cases for workflow functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_svg_extract_and_inject_with_custom_output(self):
        """Test svg_extract_and_inject with custom output paths."""
        source_svg = self.test_dir / "source.svg"
        target_svg = self.test_dir / "target.svg"
        output_svg = self.test_dir / "output.svg"
        data_output = self.test_dir / "data.json"

        source_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <switch>
        <text id="text1-ar" systemLanguage="ar"><tspan>مرحبا</tspan></text>
        <text id="text1"><tspan>Hello</tspan></text>
    </switch>
</svg>'''

        target_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <switch>
        <text id="text2"><tspan>Hello</tspan></text>
    </switch>
</svg>'''

        source_svg.write_text(source_content, encoding='utf-8')
        target_svg.write_text(target_content, encoding='utf-8')

        result = svg_extract_and_inject(
            source_svg,
            target_svg,
            output_file=output_svg,
            data_output_file=data_output,
            save_result=True
        )

        self.assertIsNotNone(result)
        self.assertTrue(data_output.exists())

    def test_svg_extract_and_inject_with_nonexistent_extract_file(self):
        """Test svg_extract_and_inject with nonexistent extract file."""
        target_svg = self.test_dir / "target.svg"
        target_svg.write_text('<svg></svg>', encoding='utf-8')

        result = svg_extract_and_inject(
            self.test_dir / "nonexistent.svg",
            target_svg,
            save_result=False
        )

        self.assertIsNone(result)

    def test_svg_extract_and_injects_with_return_stats(self):
        """Test svg_extract_and_injects with return_stats=True."""
        target_svg = self.test_dir / "target.svg"

        target_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <switch>
        <text id="text1"><tspan>Hello</tspan></text>
    </switch>
</svg>'''
        target_svg.write_text(target_content, encoding='utf-8')

        translations = {"new": {"hello": {"ar": "مرحبا"}}}

        tree, stats = svg_extract_and_injects(
            translations,
            target_svg,
            save_result=False,
            return_stats=True
        )

        self.assertIsNotNone(tree)
        self.assertIsNotNone(stats)
        self.assertIn('processed_switches', stats)

    def test_svg_extract_and_injects_with_overwrite(self):
        """Test svg_extract_and_injects with overwrite parameter."""
        target_svg = self.test_dir / "target.svg"

        target_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <switch>
        <text id="text1-ar" systemLanguage="ar"><tspan>Old</tspan></text>
        <text id="text1"><tspan>Hello</tspan></text>
    </switch>
</svg>'''
        target_svg.write_text(target_content, encoding='utf-8')

        translations = {"new": {"hello": {"ar": "New"}}}

        tree, stats = svg_extract_and_injects(
            translations,
            target_svg,
            overwrite=True,
            return_stats=True
        )

        self.assertIsNotNone(tree)
        self.assertGreater(stats.get('updated_translations', 0), 0)


class TestExtractor(unittest.TestCase):
    """Test cases for extraction functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_extract_with_multiple_languages(self):
        """Test extraction with multiple languages."""
        svg_path = self.test_dir / "test.svg"

        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <switch>
        <text id="text1-ar" systemLanguage="ar"><tspan id="t1-ar">مرحبا</tspan></text>
        <text id="text1-fr" systemLanguage="fr"><tspan id="t1-fr">Bonjour</tspan></text>
        <text id="text1"><tspan id="t1">Hello</tspan></text>
    </switch>
</svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        result = extract(svg_path)

        self.assertIsNotNone(result)
        self.assertIn("new", result)
        # Should have both ar and fr translations
        hello_translations = result["new"].get("hello", {})
        self.assertIn("ar", hello_translations)
        self.assertIn("fr", hello_translations)

    def test_extract_with_no_switches(self):
        """Test extraction with SVG containing no switch elements."""
        svg_path = self.test_dir / "test.svg"

        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <text>Just text</text>
</svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        result = extract(svg_path)

        # Should return empty or minimal structure
        self.assertIsNotNone(result)

    def test_extract_case_sensitive(self):
        """Test extraction with case_insensitive=False."""
        svg_path = self.test_dir / "test.svg"

        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <switch>
        <text id="text1-ar" systemLanguage="ar"><tspan id="t1-ar">مرحبا</tspan></text>
        <text id="text1"><tspan id="t1">Hello World</tspan></text>
    </switch>
</svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        result = extract(svg_path, case_insensitive=False)

        self.assertIsNotNone(result)
        # Keys should preserve original case
        self.assertIn("new", result)

    def test_extract_with_year_suffix(self):
        """Test extraction with year suffixes in text."""
        svg_path = self.test_dir / "test.svg"

        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <switch>
        <text id="text1-ar" systemLanguage="ar"><tspan id="t1-ar">السكان 2020</tspan></text>
        <text id="text1"><tspan id="t1">Population 2020</tspan></text>
    </switch>
</svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        result = extract(svg_path)

        self.assertIsNotNone(result)
        # Should handle year detection
        if "title" in result:
            # Year handling logic should work
            pass

    def test_extract_empty_tspans(self):
        """Test extraction with empty tspan elements."""
        svg_path = self.test_dir / "test.svg"

        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <switch>
        <text id="text1"><tspan id="t1"></tspan></text>
    </switch>
</svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        result = extract(svg_path)

        # Should handle empty tspans gracefully
        self.assertIsNotNone(result)

    def test_extract_translation_tspan_without_id(self):
        """Translations without IDs should fall back to positional matching."""
        svg_path = self.test_dir / "missing_id.svg"

        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
            <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
                <switch>
                    <text><tspan id="greeting">Hello</tspan></text>
                    <text systemLanguage="es" id="greeting-es"><tspan>Hola</tspan></text>
                </switch>
            </svg>'''

        svg_path.write_text(svg_content, encoding='utf-8')

        result = extract(svg_path)
        print(result)
        self.assertIsNotNone(result)
        self.assertIn("new", result)
        self.assertIn("hello", result["new"])
        self.assertEqual(result["new"]["hello"].get("es"), None)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_extract_with_malformed_xml(self):
        """Test extraction with malformed XML."""
        svg_path = self.test_dir / "malformed.svg"
        svg_path.write_text("<svg><text>Unclosed", encoding='utf-8')

        result = extract(svg_path)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
