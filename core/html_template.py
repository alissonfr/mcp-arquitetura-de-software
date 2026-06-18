import html

BASE_CSS = """
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: #f1f5f9;
    color: #1e293b;
    line-height: 1.6;
  }
  .container { max-width: 920px; margin: 0 auto; padding: 32px 20px 64px; }
  .report-header {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #fff;
    padding: 32px;
    border-radius: 16px;
    box-shadow: 0 10px 30px rgba(99,102,241,.25);
    margin-bottom: 28px;
  }
  .report-header h1 { margin: 0 0 8px; font-size: 1.6rem; }
  .report-header .subtitle { margin: 4px 0; font-size: 1rem; opacity: .95; }
  .report-header .meta { margin: 10px 0 0; font-size: .85rem; opacity: .85; }
  .card {
    background: #fff;
    border-radius: 14px;
    padding: 24px 28px;
    margin-bottom: 22px;
    box-shadow: 0 1px 3px rgba(15,23,42,.08), 0 8px 24px rgba(15,23,42,.04);
  }
  .card h2 { margin-top: 0; font-size: 1.2rem; border-bottom: 2px solid #eef2ff; padding-bottom: 10px; }
  .stats { display: flex; flex-wrap: wrap; gap: 14px; }
  .stat { flex: 1 1 150px; background: #f8fafc; border-radius: 12px; padding: 16px; text-align: center; border: 1px solid #eef2f7; }
  .stat-num { display: block; font-size: 1.8rem; font-weight: 700; }
  .stat-label { font-size: .78rem; color: #64748b; text-transform: uppercase; letter-spacing: .04em; }
  .stat-revision .stat-num { color: #d97706; }
  .stat-valid .stat-num { color: #059669; }
  .stat-obsolete .stat-num { color: #64748b; }
  .adr-item { padding: 18px 0; border-bottom: 1px solid #f1f5f9; }
  .adr-item:last-child { border-bottom: none; }
  .adr-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 6px; }
  .adr-head h3 { margin: 0; font-size: 1.05rem; }
  .badge { display: inline-block; padding: 4px 12px; border-radius: 999px; font-size: .78rem; font-weight: 600; white-space: nowrap; }
  .badge-revision, .badge-modified { background: #fef3c7; color: #92400e; }
  .badge-valid, .badge-added { background: #d1fae5; color: #065f46; }
  .badge-obsolete { background: #e2e8f0; color: #475569; }
  .badge-removed { background: #fee2e2; color: #991b1b; }
  .badge-unchanged { background: #f1f5f9; color: #64748b; }
  .field { margin: 8px 0; }
  .field strong { color: #475569; }
  .legend { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
  .chip { display: inline-flex; align-items: center; padding: 4px 12px; border-radius: 999px; font-size: .8rem; font-weight: 600; }
  .chip-added { background: #ecfdf5; color: #065f46; }
  .chip-removed { background: #fef2f2; color: #991b1b; }
  .chip-modified { background: #fffbeb; color: #92400e; }
  .section-title { margin: 18px 0 8px; font-size: .85rem; color: #475569; text-transform: uppercase; letter-spacing: .05em; font-weight: 700; }
  .diff { border-radius: 10px; padding: 12px 16px; margin: 8px 0; border-left: 4px solid; font-size: .92rem; }
  .diff-added { background: #ecfdf5; border-color: #10b981; }
  .diff-removed { background: #fef2f2; border-color: #ef4444; }
  .diff-label { display: block; font-size: .72rem; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 6px; }
  .diff-added .diff-label { color: #059669; }
  .diff-removed .diff-label { color: #dc2626; }
  .diff-pair { border-left: 4px solid #f59e0b; background: #fffbeb; border-radius: 10px; padding: 8px 14px; margin: 10px 0; }
  .diff-pair .diff { margin: 6px 0; border-left-width: 3px; }
  .note { color: #64748b; font-size: .9rem; }
  .empty { color: #94a3b8; font-style: italic; }
"""


def escape(text: str) -> str:
    return html.escape(text or "")


def nl2br(text: str) -> str:
    return escape(text).replace("\n", "<br>")


def render_page(title: str, body: str) -> str:
    return (
        "<!DOCTYPE html>\n"
        '<html lang="pt-BR">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{escape(title)}</title>\n"
        f"<style>{BASE_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        f'<div class="container">\n{body}\n</div>\n'
        "</body>\n"
        "</html>\n"
    )
