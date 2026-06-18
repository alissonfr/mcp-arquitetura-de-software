from openai import OpenAI
import logging

from core import convert_pdf_to_markdown, parse_all_adrs, assess_viability, write_viability_report

logger = logging.getLogger(__name__)


def run_viability_assessment(client: OpenAI, improvement: str, pdf_path: str) -> dict:
    logger.info(f"Iniciando avaliação de viabilidade para: {improvement}")

    md_text = convert_pdf_to_markdown(pdf_path)
    adrs = parse_all_adrs(md_text)

    if not adrs:
        return {
            "erro": "Nenhuma ADR encontrada no documento de arquitetura.",
            "dica": f"Verifique se o arquivo '{pdf_path}' existe e contém ADRs no formato esperado."
        }

    logger.info(f"Carregada(s) {len(adrs)} ADR(s); consultando IA...")
    data = assess_viability(client, improvement, adrs)
    data["arquivo_gerado"] = write_viability_report(data)
    return data
