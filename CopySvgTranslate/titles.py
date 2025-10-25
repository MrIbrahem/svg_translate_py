
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def make_title_translations(
    new: Dict[str, Dict[str, str]]
) -> Dict[str, Dict[str, str]]:
    all_mappings_title = {}

    for key, mapping in list(new.items()):
        year = key[-4:]
        if not key or key == year or not year.isdigit():
            continue

        all_valid = all(value[-4:].isdigit() and value[-4:] == year for value in mapping.values())

        if all_valid:
            # all_mappings_title[year] = { lang: text[:-4] for lang, text in mapping.items() }
            all_mappings_title[key[:-4].strip()] = {
                lang: text[:-4].strip()
                for lang, text in mapping.items()
            }

    return all_mappings_title


def get_titles_translations(
    all_mappings_title: Dict,
    default_texts: list[str],
)-> Dict:

    titles_translations = {}

    for text in default_texts:
        if text[-4:].isdigit():
            year = text[-4:]
            key = text[:-4]
            translations = all_mappings_title.get(key) or all_mappings_title.get(key.strip())
            if translations:
                titles_translations[text] = {lang: f"{value} {year}" for lang, value in translations.items()}

    return titles_translations
