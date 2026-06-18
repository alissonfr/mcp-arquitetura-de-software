import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

OUTPUTS_DIR = "outputs"

_CHANGE_TYPE_LABELS = {
    "adicao": "Adição",
    "remocao": "Remoção",
    "modificacao": "Modificação",
}


def _ensure_dir() -> None:
    os.makedirs(OUTPUTS_DIR, exist_ok=True)


def _timestamp_file() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _now_readable() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def _write(filename: str, content: str) -> str:
    _ensure_dir()
    path = os.path.join(OUTPUTS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Relatório gravado em: {path}")
    return path


# --------------------------------------------------------------------------- #
# Ferramenta 1 — Avaliação de Viabilidade
# O Markdown já vem pronto da IA; aqui apenas gravamos em arquivo.
# --------------------------------------------------------------------------- #

def write_viability_report(markdown: str) -> str:
    filename = f"viabilidade_{_timestamp_file()}.md"
    return _write(filename, markdown)


# --------------------------------------------------------------------------- #
# Ferramenta 2 — Changelog de ADR
# Sem IA: o diff vem como dict estruturado e é renderizado aqui em Markdown.
# --------------------------------------------------------------------------- #

def _blockquote(text: str) -> str:
    return "\n".join(f"> {line}" for line in text.splitlines())


def _render_changelog_markdown(data: dict) -> str:
    lines = []
    adr_id = data.get("id_adr", "ADR")
    lines.append(f"# Changelog — {adr_id}\n")
    lines.append(f"**Gerado em:** {_now_readable()}  ")
    lines.append(f"**Resumo:** {data.get('resumo', '')}\n")

    by_type = data.get("mudancas_por_tipo", {})
    lines.append("| Tipo de mudança | Quantidade |")
    lines.append("|-----------------|------------|")
    lines.append(f"| Adições | {by_type.get('adicao', 0)} |")
    lines.append(f"| Remoções | {by_type.get('remocao', 0)} |")
    lines.append(f"| Modificações | {by_type.get('modificacao', 0)} |\n")

    for entry in data.get("changelog", []):
        secao = entry.get("secao", "")
        lines.append(f"## {secao}\n")

        if not entry.get("possui_mudancas"):
            lines.append("_Nenhuma mudança nesta seção._\n")
            continue

        for change in entry.get("mudancas", []):
            tipo = change.get("tipo", "")
            label = _CHANGE_TYPE_LABELS.get(tipo, tipo)
            lines.append(f"### {label}\n")

            antigo = change.get("conteudo_antigo")
            novo = change.get("conteudo_novo")

            if antigo:
                lines.append("**Antes:**\n")
                lines.append(_blockquote(antigo) + "\n")
            if novo:
                lines.append("**Depois:**\n")
                lines.append(_blockquote(novo) + "\n")

    return "\n".join(lines)


def write_changelog_report(data: dict) -> str:
    adr_id = data.get("id_adr", "ADR")
    filename = f"changelog_{adr_id}_{_timestamp_file()}.md"
    return _write(filename, _render_changelog_markdown(data))
