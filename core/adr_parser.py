import re
import logging

logger = logging.getLogger(__name__)

SECTIONS = ["Contexto", "Decisão", "Status", "Consequências"]

# Cabeçalho de seção em qualquer formato: **Contexto:** | Contexto: | Contexto
# `name` é um fragmento de regex cru (ex.: "Decis[aã]o"), então NÃO pode ser escapado.
_HDR = r"(?:\*\*)?{name}:?(?:\*\*)?\s*"


def _hdr(name: str) -> str:
    return _HDR.format(name=name)


def parse_all_adrs(md_text: str) -> dict[str, dict]:
    # Divide o texto antes de cada cabeçalho de ADR: "4.1. ADR-01:", "## ADR-01:" ou "ADR-01:"
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

    # Título: texto na mesma linha após "ADR-XX:"
    title_match = re.search(r"ADR-\d+[:\s]+(.+?)(?:\n|$)", block)

    # Contexto: até o cabeçalho Decisão (ou fim do bloco)
    context_match = re.search(
        _hdr("Contexto") + r"(.*?)(?=" + _hdr("Decis[aã]o") + r"|\Z)",
        block, re.DOTALL | re.IGNORECASE
    )

    # Decisão: até Status ou Consequências (ou fim do bloco)
    decision_match = re.search(
        _hdr("Decis[aã]o") + r"(.*?)(?="
        + _hdr("Status") + r"|" + _hdr("Consequ[eê]ncias") + r"|\Z)",
        block, re.DOTALL | re.IGNORECASE
    )

    # Status: opcional (ausente no documento do SARC), só até o fim da linha
    status_match = re.search(
        _hdr("Status") + r"(.+?)(?=\n|$)",
        block, re.IGNORECASE
    )

    # Consequências: até o fim do bloco
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


def adr_to_sections(adr: dict | None) -> dict[str, str]:
    # Converte um ADR já parseado em {Contexto, Decisão, Status, Consequências};
    # ADR ausente (None) vira seções vazias — usado no diff do changelog.
    if not adr:
        return {section: "" for section in SECTIONS}
    return {
        "Contexto": adr.get("contexto") or "",
        "Decisão": adr.get("decisao") or "",
        "Status": adr.get("status") or "",
        "Consequências": adr.get("consequencias") or "",
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
