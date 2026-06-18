from markitdown import MarkItDown
import logging

logger = logging.getLogger(__name__)

_cache: dict[str, str] = {}
_converter = MarkItDown()


def convert_pdf_to_markdown(pdf_path: str) -> str:
    if pdf_path in _cache:
        logger.info(f"usando cache para: {pdf_path}")
        return _cache[pdf_path]

    logger.info(f"convertendo PDF para markdown: {pdf_path}")
    result = _converter.convert(pdf_path)
    markdown = result.text_content

    _cache[pdf_path] = markdown
    logger.info("conversão concluída com sucesso")

    return markdown
