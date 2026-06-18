import difflib
import re
import logging
from datetime import datetime

from core import parse_adr_sections, SECTIONS, write_changelog_report

logger = logging.getLogger(__name__)


def _diff_section(section_name: str, old_text: str, new_text: str) -> dict:
    if old_text == new_text:
        return {"secao": section_name, "possui_mudancas": False, "mudancas": []}

    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)

    matcher = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)

    mudancas = []
    for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
        if opcode == "equal":
            continue

        old_chunk = "".join(old_lines[i1:i2]).strip() or None
        new_chunk = "".join(new_lines[j1:j2]).strip() or None

        if opcode == "insert":
            tipo = "adicao"
        elif opcode == "delete":
            tipo = "remocao"
        else:  # replace
            tipo = "modificacao"

        mudancas.append({
            "tipo": tipo,
            "conteudo_antigo": old_chunk,
            "conteudo_novo": new_chunk,
        })

    return {
        "secao": section_name,
        "possui_mudancas": True,
        "mudancas": mudancas,
    }


def run_changelog_generation(old_version: str, new_version: str) -> dict:
    logger.info("Iniciando geração de changelog de ADR")

    old_sections = parse_adr_sections(old_version)
    new_sections = parse_adr_sections(new_version)

    id_match = re.search(r"(ADR-\d+)", new_version)
    adr_id = id_match.group(1) if id_match else "ADR-DESCONHECIDA"

    changelog = []
    total_changes = 0
    changes_by_type: dict[str, int] = {"adicao": 0, "remocao": 0, "modificacao": 0}

    for section in SECTIONS:
        old_text = old_sections.get(section, "")
        new_text = new_sections.get(section, "")

        result = _diff_section(section, old_text, new_text)
        changelog.append(result)

        if result["possui_mudancas"]:
            for change in result["mudancas"]:
                tipo = change["tipo"]
                changes_by_type[tipo] += 1
                total_changes += 1

    sections_with_changes = sum(1 for e in changelog if e["possui_mudancas"])

    result = {
        "id_adr": adr_id,
        "gerado_em": datetime.now().isoformat(),
        "secoes_analisadas": SECTIONS,
        "changelog": changelog,
        "resumo": f"{total_changes} mudança(s) detectada(s) em {sections_with_changes} seção(ões)",
        "total_mudancas": total_changes,
        "mudancas_por_tipo": changes_by_type,
    }

    result["arquivo_gerado"] = write_changelog_report(result)
    return result
