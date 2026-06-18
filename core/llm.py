from openai import OpenAI
import json
import re
import logging

from core.adr_parser import format_adrs_for_prompt

logger = logging.getLogger(__name__)

MODEL = "gpt-4.1-mini"


def connect(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


def _extract_json(content: str) -> dict:
    md_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
    if md_match:
        return json.loads(md_match.group(1))

    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        raise ValueError("Nenhum JSON encontrado na resposta da IA")
    return json.loads(match.group(0))


def assess_viability(client: OpenAI, improvement: str, adrs: dict) -> dict:
    formatted_adrs = format_adrs_for_prompt(adrs)

    prompt = f"""
      Você é um arquiteto de software sênior especializado em Architecture Decision Records (ADRs)
      e arquitetura evolutiva.

      ## Tarefa
      Analise o impacto da seguinte melhoria futura proposta sobre as ADRs existentes do
      sistema SARC (Sistema de Auxílio para Representantes Comerciais):

      **Melhoria Proposta:** {improvement}

      ## ADRs do Sistema SARC
      {formatted_adrs}

      ## Instruções de Análise
      Para CADA ADR listada acima, você DEVE:

      1. Considerar seu Contexto, Decisão, Status e Consequências
      2. Raciocinar sobre como "{improvement}" interage com a ADR
      3. Classificar usando exatamente um destes valores:
        - "precisa_revisao": a melhoria conflita diretamente ou altera significativamente esta decisão
        - "continua_valida": a melhoria não afeta esta ADR — ela permanece totalmente aplicável
        - "pode_se_tornar_obsoleta": a melhoria tornaria esta ADR não mais relevante
      4. Escrever uma justificativa concisa (2-3 frases)
      5. Escrever uma ação recomendada (1-2 frases)

      Identifique também quaisquer novas ADRs que precisariam ser criadas para suportar a melhoria.

      ## Formato de Saída
      Retorne APENAS JSON válido com exatamente esta estrutura — sem markdown, sem explicações:
      {{
        "melhoria": "<o texto da melhoria>",
        "analise": [
          {{
            "id_adr": "<ADR-XX>",
            "titulo": "<título da ADR>",
            "classificacao": "<precisa_revisao|continua_valida|pode_se_tornar_obsoleta>",
            "justificativa": "<justificativa em 2-3 frases>",
            "acao_recomendada": "<ação em 1-2 frases>"
          }}
        ],
        "novas_adrs_sugeridas": [
          {{
            "titulo": "<título da ADR sugerida>",
            "justificativa": "<por que esta nova ADR é necessária>"
          }}
        ],
        "resumo_executivo": "<resumo de 3-5 frases sobre o impacto geral>",
        "total_adrs_analisadas": <inteiro>,
        "quantidade_revisao": <inteiro>,
        "quantidade_validas": <inteiro>,
        "quantidade_obsoletas": <inteiro>
      }}
    """

    logger.info(f"Chamando IA para avaliar viabilidade: {improvement[:50]}...")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    return _extract_json(response.choices[0].message.content)
