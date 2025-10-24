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

from CopySvgTranslate import inject, normalize_text, generate_unique_id, start_injects
from CopySvgTranslate.injection.injector import load_all_mappings
from CopySvgTranslate.injection.preparation import (
    normalize_lang,
    get_text_content,
    clone_element,
    make_translation_ready,
    SvgStructureException,
)


class TestTextUtils(unittest.TestCase):
    """Test cases for text utility functions."""

    def test_normalize_text_with_tabs_and_newlines(self):
        """Test normalization with tabs and newlines."""
        self.assertEqual(normalize_text("hello\t\nworld"), "hello world")
        self.assertEqual(normalize_text("  hello\n\n  world  "), "hello world")

    def test_normalize_text_case_insensitive(self):
        """Test case-insensitive normalization."""
        self.assertEqual(normalize_text("Hello World", case_insensitive=True), "hello world")
        self.assertEqual(normalize_text("HELLO WORLD", case_insensitive=True), "hello world")
        self.assertEqual(normalize_text("HeLLo WoRLd", case_insensitive=True), "hello world")

    def test_normalize_text_unicode(self):
        """Test normalization with Unicode characters."""
        self.assertEqual(normalize_text("  مرحبا  بك  "), "مرحبا بك")
        self.assertEqual(normalize_text("  你好  世界  "), "你好 世界")


class TestPreparation(unittest.TestCase):
    """Test cases for SVG preparation functions."""

    def test_normalize_lang_simple(self):
        """Test normalizing simple language codes."""
        self.assertEqual(normalize_lang("en"), "en")
        self.assertEqual(normalize_lang("AR"), "ar")
        self.assertEqual(normalize_lang("FR"), "fr")

    def test_normalize_lang_with_region(self):
        """Test normalizing language codes with regions."""
        self.assertEqual(normalize_lang("en_US"), "en-US")
        self.assertEqual(normalize_lang("en-GB"), "en-GB")
        self.assertEqual(normalize_lang("zh_CN"), "zh-CN")

    def test_normalize_lang_complex(self):
        """Test normalizing complex language codes."""
        self.assertEqual(normalize_lang("en_US_POSIX"), "en-US-Posix")
        self.assertEqual(normalize_lang("sr_Latn_RS"), "sr-Latn-RS")

    def test_normalize_lang_empty(self):
        """Test normalizing empty language code."""
        self.assertEqual(normalize_lang(""), "")
        self.assertEqual(normalize_lang(None), None)

    def test_get_text_content(self):
        """Test getting text content from elements."""
        svg_ns = "http://www.w3.org/2000/svg"
        element = etree.fromstring(
            f'''<text xmlns="{svg_ns}">
                Hello <tspan>World</tspan> Test
            </text>'''
        )
        result = get_text_content(element)
        self.assertIn("Hello", result)
        self.assertIn("World", result)

    def test_clone_element(self):
        """Test cloning an element."""
        svg_ns = "http://www.w3.org/2000/svg"
        original = etree.fromstring(
            f'<text xmlns="{svg_ns}" id="test">Content</text>'
        )
        cloned = clone_element(original)

        self.assertEqual(original.get("id"), cloned.get("id"))
        self.assertEqual(original.text, cloned.text)
        # Verify they are different objects
        self.assertIsNot(original, cloned)

    def test_svg_structure_exception(self):
        """Test SvgStructureException creation."""
        exc = SvgStructureException("test-code", extra="Extra info")
        self.assertEqual(exc.code, "test-code")
        self.assertEqual(exc.extra, "Extra info")
        self.assertIn("test-code", str(exc))
        self.assertIn("Extra info", str(exc))

    def test_make_translation_ready_nonexistent_file(self):
        """Test make_translation_ready with nonexistent file."""
        with self.assertRaises(FileNotFoundError):
            make_translation_ready(Path("/nonexistent/file.svg"))

    def test_make_translation_ready_with_valid_svg(self):
        """Test make_translation_ready with valid SVG."""
        test_dir = Path(tempfile.mkdtemp())
        svg_path = test_dir / "test.svg"

        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.0" width="100" height="100">
    <switch>
        <text id="text1"><tspan>Hello</tspan></text>
    </switch>
</svg>'''

        svg_path.write_text(svg_content, encoding='utf-8')

        try:
            tree, root = make_translation_ready(svg_path)
            self.assertIsNotNone(tree)
            self.assertIsNotNone(root)
        finally:
            svg_path.unlink()
            test_dir.rmdir()


class TestInjector(unittest.TestCase):
    """Test cases for injection functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_load_all_mappings_single_file(self):
        """Test loading a single mapping file."""
        mapping_file = self.test_dir / "mapping.json"
        test_mapping = {"new": {"hello": {"ar": "مرحبا"}}}

        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(test_mapping, f, ensure_ascii=False)

        result = load_all_mappings([mapping_file])
        self.assertIn("new", result)
        self.assertEqual(result["new"]["hello"]["ar"], "مرحبا")

    def test_load_all_mappings_multiple_files(self):
        """Test loading multiple mapping files."""
        mapping1 = self.test_dir / "mapping1.json"
        mapping2 = self.test_dir / "mapping2.json"

        with open(mapping1, 'w', encoding='utf-8') as f:
            json.dump({"key1": {"value": 1}}, f)

        with open(mapping2, 'w', encoding='utf-8') as f:
            json.dump({"key2": {"value": 2}}, f)

        result = load_all_mappings([mapping1, mapping2])
        self.assertIn("key1", result)
        self.assertIn("key2", result)

    def test_load_all_mappings_nonexistent_file(self):
        """Test loading with nonexistent file."""
        result = load_all_mappings([self.test_dir / "nonexistent.json"])
        self.assertEqual(result, {})

    def test_load_all_mappings_invalid_json(self):
        """Test loading with invalid JSON."""
        invalid_file = self.test_dir / "invalid.json"
        invalid_file.write_text("{ invalid json", encoding='utf-8')

        result = load_all_mappings([invalid_file])
        self.assertEqual(result, {})

    def test_load_all_mappings_merge_behavior(self):
        """Test that mappings are merged correctly."""
        mapping1 = self.test_dir / "mapping1.json"
        mapping2 = self.test_dir / "mapping2.json"

        with open(mapping1, 'w', encoding='utf-8') as f:
            json.dump({"key": {"lang1": "value1"}}, f)

        with open(mapping2, 'w', encoding='utf-8') as f:
            json.dump({"key": {"lang2": "value2"}}, f)

        result = load_all_mappings([mapping1, mapping2])
        # Both languages should be present under the same key
        self.assertIn("lang1", result["key"])
        self.assertIn("lang2", result["key"])

    def test_generate_unique_id_empty_base(self):
        """Test unique ID generation with empty base ID."""
        result = generate_unique_id("", "ar", set())
        self.assertEqual(result, "-ar")

    def test_generate_unique_id_with_special_characters(self):
        """Test unique ID generation with special characters in base."""
        result = generate_unique_id("text-123", "fr", set())
        self.assertEqual(result, "text-123-fr")

    def test_inject_with_all_mappings_parameter(self):
        """Test inject using all_mappings parameter instead of mapping_files."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <switch>
        <text id="text1"><tspan>Hello</tspan></text>
    </switch>
</svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        mappings = {"new": {"hello": {"ar": "مرحبا"}}}
        tree, stats = inject(svg_path, all_mappings=mappings, return_stats=True)

        self.assertIsNotNone(tree)
        self.assertIsNotNone(stats)

    def test_inject_with_output_dir(self):
        """Test inject with output_dir parameter."""
        svg_path = self.test_dir / "test.svg"
        output_dir = self.test_dir / "output"
        output_dir.mkdir()

        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <switch>
        <text id="text1"><tspan>Hello</tspan></text>
    </switch>
</svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        mappings = {"new": {"hello": {"ar": "مرحبا"}}}
        tree = inject(
            svg_path,
            all_mappings=mappings,
            output_dir=output_dir,
            save_result=True
        )

        self.assertIsNotNone(tree)
        output_file = output_dir / "test.svg"
        self.assertTrue(output_file.exists())

    def test_inject_case_sensitive(self):
        """Test inject with case_insensitive=False."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <switch>
        <text id="text1"><tspan>Hello</tspan></text>
    </switch>
</svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        # Use exact case match
        mappings = {"new": {"Hello": {"ar": "مرحبا"}}}
        tree, stats = inject(
            svg_path,
            all_mappings=mappings,
            case_insensitive=False,
            return_stats=True
        )

        self.assertIsNotNone(tree)
        self.assertEqual(stats['inserted_translations'], 1)


class TestBatch(unittest.TestCase):
    """Test cases for batch processing functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_start_injects_single_file(self):
        """Test batch injection with a single file."""
        svg_file = self.test_dir / "test.svg"
        output_dir = self.test_dir / "output"
        output_dir.mkdir()

        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <switch>
        <text id="text1"><tspan>Hello</tspan></text>
    </switch>
</svg>'''
        svg_file.write_text(svg_content, encoding='utf-8')

        translations = {"new": {"hello": {"ar": "مرحبا"}}}

        result = start_injects(
            [svg_file],
            translations,
            output_dir,
            overwrite=False
        )

        self.assertEqual(result['saved_done'], 1)
        self.assertEqual(result['no_save'], 0)

    def test_start_injects_multiple_files(self):
        """Test batch injection with multiple files."""
        svg1 = self.test_dir / "test1.svg"
        svg2 = self.test_dir / "test2.svg"
        output_dir = self.test_dir / "output"
        output_dir.mkdir()

        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <switch>
        <text id="text1"><tspan>Hello</tspan></text>
    </switch>
</svg>'''

        svg1.write_text(svg_content, encoding='utf-8')
        svg2.write_text(svg_content, encoding='utf-8')

        translations = {"new": {"hello": {"ar": "مرحبا"}}}

        result = start_injects(
            [svg1, svg2],
            translations,
            output_dir
        )

        self.assertEqual(result['saved_done'], 2)
        self.assertIn('test1.svg', result['files'])
        self.assertIn('test2.svg', result['files'])

    def test_start_injects_with_nonexistent_file(self):
        """Test batch injection with nonexistent file."""
        output_dir = self.test_dir / "output"
        output_dir.mkdir()

        translations = {"new": {"hello": {"ar": "مرحبا"}}}

        result = start_injects(
            [self.test_dir / "nonexistent.svg"],
            translations,
            output_dir
        )

        self.assertEqual(result['saved_done'], 0)
        self.assertEqual(result['no_save'], 1)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_normalize_text_with_only_whitespace(self):
        """Test normalization with only whitespace."""
        self.assertEqual(normalize_text("   "), "")
        self.assertEqual(normalize_text("\n\t  "), "")

    def test_generate_unique_id_with_many_collisions(self):
        """Test unique ID generation with many existing IDs."""
        existing = {f"id-ar-{i}" for i in range(100)}
        existing.add("id-ar")

        result = generate_unique_id("id", "ar", existing)
        self.assertEqual(result, "id-ar-100")

    def test_inject_with_empty_mappings(self):
        """Test injection with empty mappings."""
        svg_path = self.test_dir / "test.svg"

        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <text>Test</text>
</svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        result = inject(svg_path, all_mappings={})

        # Should return None or error
        self.assertIsNone(result)

    def test_inject_return_stats_false(self):
        """Test inject with return_stats=False."""
        svg_path = self.test_dir / "test.svg"

        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <switch>
        <text id="text1"><tspan>Hello</tspan></text>
    </switch>
</svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        mappings = {"new": {"hello": {"ar": "مرحبا"}}}
        result = inject(svg_path, all_mappings=mappings, return_stats=False)

        # Should return tree only, not tuple
        self.assertIsNotNone(result)
        self.assertIsInstance(result, etree._ElementTree)


if __name__ == '__main__':
    unittest.main()
