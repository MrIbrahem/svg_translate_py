"""Utilities for extracting translation data from SVG files."""

from pathlib import Path
import logging

from lxml import etree

from ..text_utils import normalize_text, extract_text_from_node

logger = logging.getLogger(__name__)


def extract(svg_file_path, case_insensitive: bool = True):
    """Extract translations from an SVG file and return them as a dictionary."""
    svg_file_path = Path(svg_file_path)

    if not svg_file_path.exists():
        logger.error(f"SVG file not found: {svg_file_path}")
        return None

    logger.debug(f"Extracting translations from {svg_file_path}")

    parser = etree.XMLParser(remove_blank_text=True)
    try:
        tree = etree.parse(str(svg_file_path), parser)
    except (etree.XMLSyntaxError, OSError) as exc:
        logger.error(f"Failed to parse SVG file {svg_file_path}: {exc}")
        return None
    root = tree.getroot()

    switches = root.xpath('//svg:switch', namespaces={'svg': 'http://www.w3.org/2000/svg'})
    logger.debug(f"Found {len(switches)} switch elements")

    default_tspans_by_id = {}
    translations = {"new": {}}
    processed_switches = 0

    for switch in switches:
        text_elements = switch.xpath('./svg:text', namespaces={'svg': 'http://www.w3.org/2000/svg'})
        if not text_elements:
            continue

        default_texts: list[str] | None = None
        for text_elem in text_elements:
            if text_elem.get('systemLanguage'):
                continue

            tspans = text_elem.xpath('./svg:tspan', namespaces={'svg': 'http://www.w3.org/2000/svg'})
            if tspans:
                tspans_by_id = {tspan.get('id'): tspan.text.strip() for tspan in tspans if tspan.text}
                default_tspans_by_id.update(tspans_by_id)
                text_contents = [tspan.text.strip() if tspan.text else "" for tspan in tspans]
            else:
                text_contents = [text_elem.text.strip()] if text_elem.text else [""]

        if not default_texts:
            continue

        switch_translations: dict[str, list[str]] = {}
        for text_elem in text_elements:
            system_lang = text_elem.get('systemLanguage')
            if not system_lang:
                continue

            tspans = text_elem.xpath('./svg:tspan', namespaces={'svg': 'http://www.w3.org/2000/svg'})
            if tspans:
                tspans_to_id = {tspan.text.strip(): tspan.get('id') for tspan in tspans if tspan.text and tspan.text.strip() and tspan.get('id')}
                # Return a list of text from each tspan element
                text_contents = [tspan.text.strip() if tspan.text else "" for tspan in tspans]
            else:
                tspans_to_id = {}
                text_contents = [text_elem.text.strip()] if text_elem.text else [""]

            switch_translations[system_lang] = [normalize_text(text) for text in text_contents]

            for text in text_contents:
                normalized_translation = normalize_text(text)
                base_id = tspans_to_id.get(text.strip(), "")
                if not base_id:
                    continue
                    
                base_id = base_id.split("-")[0].strip()
                english_text = default_tspans_by_id.get(base_id) or default_tspans_by_id.get(
                    base_id.lower()
                )
                logger.debug(f"{base_id=}, {english_text=}")
                if not english_text:
                    continue

                store_key = english_text if english_text in translations["new"] else english_text.lower()
                if store_key in translations["new"]:
                    translations["new"][store_key][system_lang] = normalized_translation

        # If we found both default text and translations, add to our data
        if default_texts and switch_translations:
            processed_switches += 1
            logger.debug(f"Processed switch with default texts: {default_texts}")

        processed_switches += 1
        for lang, translated_texts in switch_translations.items():
            for index, default_text in enumerate(default_texts):
                if not default_text:
                    continue
                if index >= len(translated_texts):
                    logger.debug(
                        "Missing translation for '%s' in language '%s'", default_text, lang
                    )
                    continue

    translations["title"] = {}
    for key, mapping in list(translations["new"].items()):
        if key and key[-4:].isdigit():
            year = key[-4:]
            if key != year and all(value[-4:].isdigit() and value[-4:] == year for value in mapping.values()):
                translations["title"][key[:-4]] = {lang: text[:-4] for lang, text in mapping.items()}

    if not translations["new"]:
        translations.pop("new")

    logger.debug(f"Extracted translations for {processed_switches} switches")

    all_languages = set()
    for mapping in translations.get("new", {}).values():
        all_languages.update(lang for lang, text in mapping.items() if text)
    logger.debug(
        "Found translations in %d languages: %s",
        len(all_languages),
        ', '.join(sorted(all_languages)),
    )

    return translations
