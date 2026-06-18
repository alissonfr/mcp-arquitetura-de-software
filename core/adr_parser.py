import re
import logging

logger = logging.getLogger(__name__)

# Section names as they appear in the document and in the tool output (kept pt-BR).
SECTIONS = ["Contexto", "Decisão", "Status", "Consequências"]

# Section header in any format: **Contexto:** | Contexto: | Contexto
# `name` is a raw regex fragment (e.g. "Decis[aã]o"), so it must NOT be escaped.
_HDR = r"(?:\*\*)?{name}:?(?:\*\*)?\s*"


def _hdr(name: str) -> str:
    return _HDR.format(name=name)


def parse_all_adrs(md_text: str) -> dict[str, dict]:
    # Split the text before each ADR header: "4.1. ADR-01:", "## ADR-01:" or "ADR-01:"
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

    logger.info(f"Extraída(s) {len(adrs)} ADR(s) do documento")
    return adrs


def _parse_single_adr(block: str) -> dict:
    id_match = re.search(r"(ADR-\d+)", block)
    if not id_match:
        return {}

    adr_id = id_match.group(1).strip()

    # Title: text on the same line after "ADR-XX:"
    title_match = re.search(r"ADR-\d+[:\s]+(.+?)(?:\n|$)", block)

    # Context: up to the "Decisão" header (or end of block)
    context_match = re.search(
        _hdr("Contexto") + r"(.*?)(?=" + _hdr("Decis[aã]o") + r"|\Z)",
        block, re.DOTALL | re.IGNORECASE
    )

    # Decision: up to "Status" or "Consequências" (or end of block)
    decision_match = re.search(
        _hdr("Decis[aã]o") + r"(.*?)(?="
        + _hdr("Status") + r"|" + _hdr("Consequ[eê]ncias") + r"|\Z)",
        block, re.DOTALL | re.IGNORECASE
    )

    # Status: optional (absent in the SARC document), only to end of line
    status_match = re.search(
        _hdr("Status") + r"(.+?)(?=\n|$)",
        block, re.IGNORECASE
    )

    # Consequences: to the end of the block
    consequences_match = re.search(
        _hdr("Consequ[eê]ncias") + r"(.*?)(?=\Z)",
        block, re.DOTALL | re.IGNORECASE
    )

    return {
        "id": adr_id,
        "title": title_match.group(1).strip() if title_match else None,
        "context": context_match.group(1).strip() if context_match else None,
        "decision": decision_match.group(1).strip() if decision_match else None,
        "status": status_match.group(1).strip() if status_match else None,
        "consequences": consequences_match.group(1).strip() if consequences_match else None,
    }


def adr_to_sections(adr: dict | None) -> dict[str, str]:
    # Convert a parsed ADR into {Contexto, Decisão, Status, Consequências};
    # a missing ADR (None) becomes empty sections — used by the changelog diff.
    if not adr:
        return {section: "" for section in SECTIONS}
    return {
        "Contexto": adr.get("context") or "",
        "Decisão": adr.get("decision") or "",
        "Status": adr.get("status") or "",
        "Consequências": adr.get("consequences") or "",
    }


def format_adrs_for_prompt(adrs: dict) -> str:
    parts = []
    for adr in adrs.values():
        part = (
            f"### {adr['id']}: {adr['title']}\n\n"
            f"**Contexto:** {adr.get('context') or 'N/A'}\n\n"
            f"**Decisão:** {adr.get('decision') or 'N/A'}\n\n"
            f"**Consequências:**\n{adr.get('consequences') or 'N/A'}"
        )
        parts.append(part)
    return "\n\n---\n\n".join(parts)
