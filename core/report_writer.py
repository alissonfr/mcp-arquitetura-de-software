import os
import webbrowser
from pathlib import Path
from datetime import datetime
import logging

from core.html_template import render_page, escape, nl2br

logger = logging.getLogger(__name__)

OUTPUTS_DIR = "outputs"

_CLASSIFICATION = {
    "precisa_revisao": ("Precisa de revisão", "badge-revision"),
    "continua_valida": ("Continua válida", "badge-valid"),
    "pode_se_tornar_obsoleta": ("Pode se tornar obsoleta", "badge-obsolete"),
}

_SITUATION = {
    "modificada": ("Modificada", "badge-modified"),
    "adicionada": ("Adicionada", "badge-added"),
    "removida": ("Removida", "badge-removed"),
    "sem_mudancas": ("Sem alterações", "badge-unchanged"),
}


def _ensure_dir() -> None:
    os.makedirs(OUTPUTS_DIR, exist_ok=True)


def _timestamp_file() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _now_readable() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def _write_and_open(filename: str, html_content: str) -> str:
    _ensure_dir()
    path = os.path.join(OUTPUTS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info(f"Relatório gravado em: {path}")

    # Path.as_uri() gera um file:// URI válido no Windows e no Linux
    try:
        webbrowser.open(Path(path).resolve().as_uri())
        logger.info("Relatório aberto no navegador")
    except Exception as e:
        logger.warning(f"Não foi possível abrir o navegador automaticamente: {e}")

    return path


# --------------------------------------------------------------------------- #
# Tool 1 — Viability assessment
# The AI returns structured data (JSON) that we render into the HTML template.
# --------------------------------------------------------------------------- #

def _render_viability_html(data: dict) -> str:
    improvement = escape(data.get("melhoria", "N/A"))

    header = (
        '<header class="report-header">'
        "<h1>Avaliação de Viabilidade de Melhoria Futura — SARC</h1>"
        f'<p class="subtitle">Melhoria avaliada: <strong>{improvement}</strong></p>'
        f'<p class="meta">Gerado em {_now_readable()}</p>'
        "</header>"
    )

    summary = (
        '<section class="card"><h2>Resumo Executivo</h2>'
        f"<p>{escape(data.get('resumo_executivo', ''))}</p></section>"
    )

    overview = (
        '<section class="card"><h2>Visão Geral</h2><div class="stats">'
        f'<div class="stat"><span class="stat-num">{data.get("total_adrs_analisadas", 0)}</span>'
        '<span class="stat-label">ADRs analisadas</span></div>'
        f'<div class="stat stat-revision"><span class="stat-num">{data.get("quantidade_revisao", 0)}</span>'
        '<span class="stat-label">Precisam de revisão</span></div>'
        f'<div class="stat stat-valid"><span class="stat-num">{data.get("quantidade_validas", 0)}</span>'
        '<span class="stat-label">Continuam válidas</span></div>'
        f'<div class="stat stat-obsolete"><span class="stat-num">{data.get("quantidade_obsoletas", 0)}</span>'
        '<span class="stat-label">Podem se tornar obsoletas</span></div>'
        "</div></section>"
    )

    items = []
    for adr in data.get("analise", []):
        label, css = _CLASSIFICATION.get(
            adr.get("classificacao", ""),
            (adr.get("classificacao", ""), "badge-unchanged")
        )
        items.append(
            '<div class="adr-item">'
            '<div class="adr-head">'
            f"<h3>{escape(adr.get('id_adr', '?'))}: {escape(adr.get('titulo', ''))}</h3>"
            f'<span class="badge {css}">{escape(label)}</span>'
            "</div>"
            f'<p class="field"><strong>Justificativa:</strong> {escape(adr.get("justificativa", ""))}</p>'
            f'<p class="field"><strong>Ação recomendada:</strong> {escape(adr.get("acao_recomendada", ""))}</p>'
            "</div>"
        )
    analysis = '<section class="card"><h2>Análise por ADR</h2>' + "".join(items) + "</section>"

    new_adrs = data.get("novas_adrs_sugeridas", [])
    if new_adrs:
        blocks = "".join(
            f'<div class="adr-item"><div class="adr-head"><h3>{escape(n.get("titulo", ""))}</h3>'
            f'<span class="badge badge-added">Nova ADR</span></div>'
            f'<p class="field">{escape(n.get("justificativa", ""))}</p></div>'
            for n in new_adrs
        )
    else:
        blocks = '<p class="empty">Nenhuma nova ADR é necessária.</p>'
    new_adrs_html = '<section class="card"><h2>Novas ADRs Sugeridas</h2>' + blocks + "</section>"

    body = header + summary + overview + analysis + new_adrs_html
    return render_page("Avaliação de Viabilidade — SARC", body)


def write_viability_report(data: dict) -> str:
    filename = f"viabilidade_{_timestamp_file()}.html"
    return _write_and_open(filename, _render_viability_html(data))


# --------------------------------------------------------------------------- #
# Tool 2 — ADR changelog
# No AI: the diff comes as a structured dict and is rendered as colored HTML.
# --------------------------------------------------------------------------- #

def _render_diff_change(change: dict) -> str:
    change_type = change.get("tipo", "")
    old = change.get("conteudo_antigo")
    new = change.get("conteudo_novo")

    if change_type == "adicao":
        return (
            '<div class="diff diff-added"><span class="diff-label">Adição</span>'
            f"{nl2br(new)}</div>"
        )
    if change_type == "remocao":
        return (
            '<div class="diff diff-removed"><span class="diff-label">Remoção</span>'
            f"{nl2br(old)}</div>"
        )
    # modification: show "before" (red) and "after" (green) grouped together
    return (
        '<div class="diff-pair">'
        '<div class="diff diff-removed"><span class="diff-label">Antes</span>'
        f"{nl2br(old)}</div>"
        '<div class="diff diff-added"><span class="diff-label">Depois</span>'
        f"{nl2br(new)}</div>"
        "</div>"
    )


def _render_changelog_html(data: dict) -> str:
    header = (
        '<header class="report-header">'
        "<h1>Changelog de ADRs — SARC</h1>"
        '<p class="subtitle">Comparação entre duas versões do documento de arquitetura</p>'
        f'<p class="meta">Versão antiga: {escape(data.get("documento_antigo", ""))}<br>'
        f'Versão nova: {escape(data.get("documento_novo", ""))}<br>'
        f"Gerado em {_now_readable()}</p>"
        "</header>"
    )

    totals = data.get("totais", {})
    summary = (
        '<section class="card">'
        '<div class="legend">'
        '<span class="chip chip-added">Adição</span>'
        '<span class="chip chip-removed">Remoção</span>'
        '<span class="chip chip-modified">Modificação</span>'
        "</div>"
        f"<p>{escape(data.get('resumo', ''))}</p>"
        '<div class="stats">'
        f'<div class="stat stat-revision"><span class="stat-num">{totals.get("modificadas", 0)}</span>'
        '<span class="stat-label">ADRs modificadas</span></div>'
        f'<div class="stat stat-valid"><span class="stat-num">{totals.get("adicionadas", 0)}</span>'
        '<span class="stat-label">ADRs adicionadas</span></div>'
        f'<div class="stat stat-obsolete"><span class="stat-num">{totals.get("removidas", 0)}</span>'
        '<span class="stat-label">ADRs removidas</span></div>'
        f'<div class="stat"><span class="stat-num">{data.get("total_mudancas", 0)}</span>'
        '<span class="stat-label">Mudanças totais</span></div>'
        "</div></section>"
    )

    cards = []
    unchanged = []
    for adr in data.get("adrs", []):
        situation = adr.get("situacao", "sem_mudancas")
        if situation == "sem_mudancas":
            unchanged.append(adr.get("id_adr", "?"))
            continue

        label, css = _SITUATION.get(situation, (situation, "badge-unchanged"))
        sections_html = []
        for section in adr.get("secoes", []):
            if not section.get("possui_mudancas"):
                continue
            changes = "".join(_render_diff_change(c) for c in section.get("mudancas", []))
            sections_html.append(
                f'<div class="section-title">{escape(section.get("secao", ""))}</div>{changes}'
            )

        cards.append(
            '<section class="card">'
            '<div class="adr-head">'
            f"<h2>{escape(adr.get('id_adr', '?'))}: {escape(adr.get('titulo', ''))}</h2>"
            f'<span class="badge {css}">{escape(label)}</span>'
            "</div>"
            + ("".join(sections_html) or '<p class="empty">Sem detalhes de seção.</p>')
            + "</section>"
        )

    if unchanged:
        cards.append(
            '<section class="card"><p class="note">ADRs sem alterações: '
            + ", ".join(escape(i) for i in unchanged) + "</p></section>"
        )

    body = header + summary + "".join(cards)
    return render_page("Changelog de ADRs — SARC", body)


def write_changelog_report(data: dict) -> str:
    filename = f"changelog_{_timestamp_file()}.html"
    return _write_and_open(filename, _render_changelog_html(data))
