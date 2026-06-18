import difflib
import re
import logging
from datetime import datetime

from core import convert_pdf_to_markdown, parse_all_adrs, adr_to_sections, SECTIONS, write_changelog_report

logger = logging.getLogger(__name__)


def _adr_number(adr_id: str) -> int:
    match = re.search(r"\d+", adr_id)
    return int(match.group()) if match else 0


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

    return {"secao": section_name, "possui_mudancas": True, "mudancas": mudancas}


def run_changelog_generation(old_pdf_path: str, new_pdf_path: str) -> dict:
    logger.info(f"Iniciando changelog entre '{old_pdf_path}' e '{new_pdf_path}'")

    old_adrs = parse_all_adrs(convert_pdf_to_markdown(old_pdf_path))
    new_adrs = parse_all_adrs(convert_pdf_to_markdown(new_pdf_path))

    if not old_adrs and not new_adrs:
        return {
            "erro": "Nenhuma ADR encontrada nos documentos informados.",
            "dica": "Verifique se os PDFs existem e contêm ADRs no formato esperado."
        }

    all_ids = sorted(set(old_adrs) | set(new_adrs), key=_adr_number)

    adrs_result = []
    by_type = {"adicao": 0, "remocao": 0, "modificacao": 0}
    totais = {"modificadas": 0, "adicionadas": 0, "removidas": 0, "sem_mudancas": 0}
    total_mudancas = 0

    for adr_id in all_ids:
        old_adr = old_adrs.get(adr_id)
        new_adr = new_adrs.get(adr_id)

        old_sections = adr_to_sections(old_adr)
        new_sections = adr_to_sections(new_adr)

        secoes = []
        adr_changes = 0
        for section in SECTIONS:
            diff = _diff_section(section, old_sections[section], new_sections[section])
            secoes.append(diff)
            if diff["possui_mudancas"]:
                for change in diff["mudancas"]:
                    by_type[change["tipo"]] += 1
                    total_mudancas += 1
                    adr_changes += 1

        if new_adr and not old_adr:
            situacao = "adicionada"
            totais["adicionadas"] += 1
        elif old_adr and not new_adr:
            situacao = "removida"
            totais["removidas"] += 1
        elif adr_changes > 0:
            situacao = "modificada"
            totais["modificadas"] += 1
        else:
            situacao = "sem_mudancas"
            totais["sem_mudancas"] += 1

        titulo = (new_adr or old_adr).get("titulo")
        adrs_result.append({
            "id_adr": adr_id,
            "titulo": titulo,
            "situacao": situacao,
            "secoes": secoes,
        })

    resumo = (
        f"{totais['modificadas']} ADR(s) modificada(s), "
        f"{totais['adicionadas']} adicionada(s) e {totais['removidas']} removida(s)"
    )

    result = {
        "documento_antigo": old_pdf_path,
        "documento_novo": new_pdf_path,
        "gerado_em": datetime.now().isoformat(),
        "adrs": adrs_result,
        "resumo": resumo,
        "totais": totais,
        "mudancas_por_tipo": by_type,
        "total_mudancas": total_mudancas,
    }

    result["arquivo_gerado"] = write_changelog_report(result)
    return result
