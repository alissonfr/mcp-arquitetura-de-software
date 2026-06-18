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
ARCHITECTURE_FILE = "files/documento_arquitetura_sarc.pdf"

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
        "Recebe uma melhoria futura proposta para o sistema SARC e usa IA para analisar "
        "o impacto sobre cada ADR existente, indicando quais decisões precisam ser revisadas, "
        "quais continuam válidas, quais podem se tornar obsoletas e se novas ADRs são necessárias"
    )
)
def assess_improvement_viability(improvement: str) -> dict:
    return run_viability_assessment(get_client(), improvement, ARCHITECTURE_FILE)


@mcp.tool(
    name="gerar_changelog_adr",
    title="Gerador de Changelog de ADRs",
    description=(
        "Recebe duas versões de um ADR (texto antigo e texto novo) e gera um changelog "
        "estruturado com as diferenças por seção (Contexto, Decisão, Status, Consequências), "
        "classificando cada mudança como adição, remoção ou modificação"
    )
)
def generate_adr_changelog(old_version: str, new_version: str) -> dict:
    return run_changelog_generation(old_version, new_version)


if __name__ == "__main__":
    try:
        logger.info(f"Iniciando servidor MCP: {SERVER_NAME}")
        logger.info(f"Documento de arquitetura: {ARCHITECTURE_FILE}")
        mcp.run()
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor: {e}")
        raise
