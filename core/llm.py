from openai import OpenAI
from datetime import datetime
import logging

from core.adr_parser import format_adrs_for_prompt

logger = logging.getLogger(__name__)

MODEL = "gpt-4.1-mini"


def connect(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


def assess_viability(client: OpenAI, improvement: str, adrs: dict) -> str:
    formatted_adrs = format_adrs_for_prompt(adrs)
    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

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
Para CADA ADR listada acima:
1. Considere seu Contexto, Decisão, Status e Consequências
2. Raciocine sobre como "{improvement}" interage com a ADR
3. Classifique usando exatamente um destes rótulos: "Precisa de revisão",
   "Continua válida" ou "Pode se tornar obsoleta"
4. Escreva uma justificativa concisa (2-3 frases)
5. Escreva uma ação recomendada (1-2 frases)

Identifique também quaisquer novas ADRs que precisariam ser criadas para suportar a melhoria.

## Formato de Saída
Retorne APENAS um documento Markdown seguindo EXATAMENTE este modelo, sem blocos de código
e sem nenhum texto fora do modelo:

# Avaliação de Viabilidade de Melhoria Futura — SARC

**Melhoria avaliada:** {improvement}
**Gerado em:** {generated_at}

## Resumo Executivo

<resumo de 3-5 frases sobre o impacto geral da melhoria nas ADRs>

## Visão Geral

| Métrica | Valor |
|---------|-------|
| Total de ADRs analisadas | <inteiro> |
| Precisam de revisão | <inteiro> |
| Continuam válidas | <inteiro> |
| Podem se tornar obsoletas | <inteiro> |

## Análise por ADR

### ADR-XX: <título da ADR>

**Classificação:** <Precisa de revisão | Continua válida | Pode se tornar obsoleta>

**Justificativa:** <justificativa em 2-3 frases>

**Ação recomendada:** <ação em 1-2 frases>

(repita o bloco "### ADR-XX" para cada ADR analisada)

## Novas ADRs Sugeridas

### <título da nova ADR>

<justificativa de por que esta nova ADR é necessária>

(repita para cada nova ADR; se nenhuma for necessária, escreva apenas: "Nenhuma nova ADR é necessária.")
"""

    logger.info(f"Chamando IA para avaliar viabilidade: {improvement[:50]}...")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()
