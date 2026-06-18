from openai import OpenAI
from core.pdf_converter import convert_pdf_to_markdown
from core.adr_parser import parse_all_adrs
from core.report_writer import write_viability_report
from core import llm
import logging

logger = logging.getLogger(__name__)


def run_viability_assessment(client: OpenAI, improvement: str, architecture_file: str) -> dict:
    logger.info(f"iniciando avaliação de viabilidade para: {improvement}")

    md_text = convert_pdf_to_markdown(architecture_file)
    adrs = parse_all_adrs(md_text)

    if not adrs:
        return {
            "erro": "Nenhuma ADR encontrada no documento de arquitetura.",
            "dica": f"Verifique se o arquivo '{architecture_file}' existe e contém ADRs no formato esperado."
        }

    logger.info(f"{len(adrs)} ADR(s) carregada(s), consultando IA...")
    result = llm.assess_viability(client, improvement, adrs)

    result["arquivo_gerado"] = write_viability_report(result)
    return result
