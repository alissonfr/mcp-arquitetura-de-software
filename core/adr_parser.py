import re
import logging

logger = logging.getLogger(__name__)

SECTIONS = ["Contexto", "Decisão", "Status", "Consequências"]

# Matches a section header in either format:
#   **Contexto:**  or  Contexto:  or  Contexto
# `name` is a raw regex fragment (e.g. "Decis[aã]o" to tolerate accents),
# so it must NOT be escaped — escaping would turn the char class into literals.
_HDR = r"(?:\*\*)?{name}:?(?:\*\*)?\s*"


def _hdr(name: str) -> str:
    return _HDR.format(name=name)


def parse_all_adrs(md_text: str) -> dict[str, dict]:
    # Split on every ADR header regardless of prefix style:
    #   "4.1. ADR-01: Title"  (SARC LaTeX PDF via markitdown)
    #   "## ADR-01: Title"    (professor's markdown file)
    #   "ADR-01: Title"       (bare)
    blocks = re.split(
        r"(?=(?:#{1,6}\s+)?(?:\d+\.\d+[\.\s]+)?ADR-\d+[:\s])",
        md_text
    )

    adrs = {}
    for block in blocks:
        if not re.search(r"ADR-\d+", block):
            continue
        adr = _parse_single_adr(block.strip())
        if adr and adr.get("id"):
            adrs[adr["id"]] = adr

    logger.info(f"{len(adrs)} ADR(s) extraída(s) do documento")
    return adrs


def _parse_single_adr(block: str) -> dict:
    id_match = re.search(r"(ADR-\d+)", block)
    if not id_match:
        return {}

    adr_id = id_match.group(1).strip()

    # Title: text on same line after "ADR-XX:" or "ADR-XX "
    title_match = re.search(r"ADR-\d+[:\s]+(.+?)(?:\n|$)", block)

    # Context → ends at Decisão (or EOF)
    context_match = re.search(
        _hdr("Contexto") + r"(.*?)(?=" + _hdr("Decis[aã]o") + r"|\Z)",
        block, re.DOTALL | re.IGNORECASE
    )

    # Decision → ends at Status or Consequências (or EOF)
    decision_match = re.search(
        _hdr("Decis[aã]o") + r"(.*?)(?="
        + _hdr("Status") + r"|" + _hdr("Consequ[eê]ncias") + r"|\Z)",
        block, re.DOTALL | re.IGNORECASE
    )

    # Status is optional (not present in SARC document)
    status_match = re.search(
        _hdr("Status") + r"(.+?)(?=\n|$)",
        block, re.IGNORECASE
    )

    # Consequences → to end of block
    consequences_match = re.search(
        _hdr("Consequ[eê]ncias") + r"(.*?)(?=\Z)",
        block, re.DOTALL | re.IGNORECASE
    )

    return {
        "id": adr_id,
        "titulo": title_match.group(1).strip() if title_match else None,
        "contexto": context_match.group(1).strip() if context_match else None,
        "decisao": decision_match.group(1).strip() if decision_match else None,
        "status": status_match.group(1).strip() if status_match else None,
        "consequencias": consequences_match.group(1).strip() if consequences_match else None,
    }


def parse_adr_sections(adr_text: str) -> dict[str, str]:
    """Extract sections from a raw ADR text string (used by the changelog tool)."""
    context_match = re.search(
        _hdr("Contexto") + r"(.*?)(?=" + _hdr("Decis[aã]o") + r"|\Z)",
        adr_text, re.DOTALL | re.IGNORECASE
    )
    decision_match = re.search(
        _hdr("Decis[aã]o") + r"(.*?)(?="
        + _hdr("Status") + r"|" + _hdr("Consequ[eê]ncias") + r"|\Z)",
        adr_text, re.DOTALL | re.IGNORECASE
    )
    status_match = re.search(
        _hdr("Status") + r"(.+?)(?=\n|$)",
        adr_text, re.IGNORECASE
    )
    consequences_match = re.search(
        _hdr("Consequ[eê]ncias") + r"(.*?)(?=\Z)",
        adr_text, re.DOTALL | re.IGNORECASE
    )

    return {
        "Contexto": context_match.group(1).strip() if context_match else "",
        "Decisão": decision_match.group(1).strip() if decision_match else "",
        "Status": status_match.group(1).strip() if status_match else "",
        "Consequências": consequences_match.group(1).strip() if consequences_match else "",
    }


def format_adrs_for_prompt(adrs: dict) -> str:
    parts = []
    for adr in adrs.values():
        part = (
            f"### {adr['id']}: {adr['titulo']}\n\n"
            f"**Contexto:** {adr.get('contexto') or 'N/A'}\n\n"
            f"**Decisão:** {adr.get('decisao') or 'N/A'}\n\n"
            f"**Consequências:**\n{adr.get('consequencias') or 'N/A'}"
        )
        parts.append(part)
    return "\n\n---\n\n".join(parts)
