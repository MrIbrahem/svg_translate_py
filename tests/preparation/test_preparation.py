"""

pytest tests/preparation/test_preparation.py

"""

from pathlib import Path
from CopySvgTranslate import make_translation_ready

FIXTURES_DIR = Path(__file__).parent


class TestIntegrationWorkflows:

    def test_make_translation_ready(self):

        svg_new = FIXTURES_DIR / "before_translate_ready.svg"

        tree, root = make_translation_ready(FIXTURES_DIR / "before_translate.svg", write_back=False)

        tree.write(str(svg_new), pretty_print=True, xml_declaration=True, encoding="utf-8")
