import re
import unicodedata
import logging

from markitdown import MarkItDown

logger = logging.getLogger(__name__)

_cache: dict[str, str] = {}
_converter = MarkItDown()

# pdfminer (used by markitdown) extracts LaTeX-generated PDFs with spacing
# diacritics detached from their base letter (e.g. "Estrat´egia" -> "Estratégia").
# The maps below reassemble them into proper Unicode (NFC) accented characters.
_BEFORE_MARKS = {
    "´": "́",  # ´ acute
    "˜": "̃",  # ˜ small tilde
    "ˆ": "̂",  # ˆ circumflex
    "`": "̀",  # ` grave
    "¨": "̈",  # ¨ diaeresis
}
_DOTLESS = {"ı": "i", "ȷ": "j"}  # ı, ȷ -> i, j so NFC can compose


def _compose(combining: str, vowel: str) -> str:
    vowel = _DOTLESS.get(vowel, vowel)
    return unicodedata.normalize("NFC", vowel + combining)


def _fix_pdf_accents(text: str) -> str:
    # cedilla + tilde (ç + ã/õ), tolerating the spurious space: "c¸ ˜ao" -> "ção"
    text = re.sub(
        r"([cC])¸\s*˜\s*([aoAO])",
        lambda m: ("ç" if m.group(1) == "c" else "Ç") + _compose("̃", m.group(2)),
        text,
    )
    # remaining cedilla: "c¸" -> "ç"
    text = re.sub(r"([cC])¸", lambda m: "ç" if m.group(1) == "c" else "Ç", text)
    # marks placed before the vowel: "˜a" -> ã, "´o" -> ó, "´E" -> É ...
    for mark, combining in _BEFORE_MARKS.items():
        text = re.sub(
            re.escape(mark) + r"\s*([A-Za-zıȷ])",
            lambda m, c=combining: _compose(c, m.group(1)),
            text,
        )
    return text


def convert_pdf_to_markdown(pdf_path: str) -> str:
    if pdf_path in _cache:
        logger.info(f"Usando cache para: {pdf_path}")
        return _cache[pdf_path]

    logger.info(f"Convertendo PDF para markdown: {pdf_path}")
    result = _converter.convert(pdf_path)
    markdown = _fix_pdf_accents(result.text_content)

    _cache[pdf_path] = markdown
    logger.info("Conversão concluída com sucesso")

    return markdown
