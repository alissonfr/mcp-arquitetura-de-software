from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
import logging

from core import connect
from tools import run_viability_assessment, run_changelog_generation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

load_dotenv()

SERVER_NAME = "sarc-adr-tools"

mcp = FastMCP(SERVER_NAME)
logger = logging.getLogger(SERVER_NAME)

_client = None

SERVER_INFO = {
    "nome": "SARC ADR Tools",
    "descricao": "Servidor MCP com ferramentas de análise e versionamento de ADRs do sistema SARC",
    "versao": "1.0.0",
    "ferramentas": [
        "avaliar_viabilidade_melhoria",
        "gerar_changelog_adr"
    ]
}


def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        _client = connect(api_key)
    return _client


@mcp.tool(
    name="informacoes_servidor",
    title="Informações do Servidor",
    description="Retorna informações básicas sobre o servidor MCP SARC ADR Tools"
)
def server_info() -> dict:
    return SERVER_INFO


@mcp.tool(
    name="avaliar_viabilidade_melhoria",
    title="Avaliador de Viabilidade de Melhorias Futuras",
    description=(
        "Recebe uma melhoria futura proposta e o caminho do PDF do documento de arquitetura "
        "do SARC, e usa IA para analisar o impacto sobre cada ADR existente, indicando quais "
        "decisões precisam ser revisadas, quais continuam válidas, quais podem se tornar "
        "obsoletas e se novas ADRs são necessárias. Gera um relatório HTML."
    )
)
def assess_improvement_viability(improvement: str, pdf_path: str) -> dict:
    return run_viability_assessment(get_client(), improvement, pdf_path)


@mcp.tool(
    name="gerar_changelog_adr",
    title="Gerador de Changelog de ADRs",
    description=(
        "Recebe os caminhos de dois PDFs do documento de arquitetura (versão antiga e versão "
        "nova), converte ambos para markdown, casa as ADRs por identificador e gera um changelog "
        "estruturado com as diferenças por seção (Contexto, Decisão, Status, Consequências), "
        "classificando cada mudança como adição, remoção ou modificação. Gera um relatório HTML."
    )
)
def generate_adr_changelog(old_pdf_path: str, new_pdf_path: str) -> dict:
    return run_changelog_generation(old_pdf_path, new_pdf_path)


if __name__ == "__main__":
    try:
        logger.info(f"Iniciando servidor MCP: {SERVER_NAME}")
        mcp.run()
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor: {e}")
        raise
