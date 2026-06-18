from mcp.client.stdio import stdio_client
from mcp import ClientSession as session, StdioServerParameters as session_parameters
from openai import OpenAI
from dotenv import load_dotenv
import os
import sys
import asyncio
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("sarc-client")

load_dotenv()

MODEL = "gpt-4.1-mini"

SYSTEM_PROMPT = """
Você é um assistente especializado em arquitetura de software com acesso às ferramentas
MCP do sistema SARC (Sistema de Análise de Requisitos e Contratos).

Quando solicitado, utilize as ferramentas disponíveis para analisar o impacto de
melhorias futuras sobre as ADRs existentes do sistema SARC, apresentando os resultados
de forma clara e organizada.
"""

# ADR-07 do SARC: versão atual conforme o documento de arquitetura
OLD_ADR_EXAMPLE = """## ADR-07: Estratégia de Backup e Recuperação

**Contexto:**
Os requisitos RQF011 e RQF012 exigem a exportação e importação de backups da base de dados.
O RNF005 complementa determinando que exportações periódicas devem ser realizadas e os arquivos
gerados devem ser armazenados em locais seguros. É necessário garantir que backups corrompidos
não sejam importados.

**Decisão:**
Implementar um mecanismo de backup utilizando ferramentas nativas do SGBD (ex.: pg_dump),
com os arquivos armazenados no sistema de arquivos local e possibilidade de cópia para
armazenamento externo.

**Status:** Proposto

**Consequências:**
- Positiva: Proteção contra perda de dados através da realização periódica de backups da base de dados;
- Positiva: Utilização de ferramentas nativas do PostgreSQL aumenta a confiabilidade e compatibilidade do processo de restauração;
- Positiva: Verificações de integridade dos arquivos de backup reduzem o risco de importação de dados corrompidos;
- Negativa: O armazenamento contínuo de backups pode aumentar significativamente o consumo de espaço em disco;
- Negativa: O processo de exportação e restauração pode impactar o desempenho durante operações em horários de pico;
- Negativa: Dependência do sistema de arquivos local pode representar um ponto único de falha caso não exista cópia externa.
"""

# ADR-07 revisada após implementar a melhoria futura "Automatização completa dos backups
# com armazenamento em nuvem" listada na seção de Análise Crítica do documento SARC
NEW_ADR_EXAMPLE = """## ADR-07: Estratégia de Backup e Recuperação com Armazenamento em Nuvem

**Contexto:**
Os requisitos RQF011 e RQF012 exigem a exportação e importação de backups da base de dados.
O RNF005 determina que exportações periódicas devem ser realizadas e armazenadas em locais
seguros. A dependência exclusiva do sistema de arquivos local apresentou risco de ponto único
de falha, motivando a adoção de um modelo híbrido com replicação automática para nuvem.

**Decisão:**
Implementar um mecanismo de backup automático utilizando ferramentas nativas do SGBD (pg_dump),
com armazenamento primário local e replicação automática para armazenamento em nuvem (AWS S3 ou
equivalente). O processo de backup será agendado e executado automaticamente, com verificação de
integridade e notificação em caso de falhas.

**Status:** Aceito

**Consequências:**
- Positiva: Eliminação do ponto único de falha com backup redundante em nuvem;
- Positiva: Automação completa reduz intervenção humana e risco de esquecimento de backups manuais;
- Positiva: Proteção geográfica dos dados em caso de desastres físicos no local;
- Positiva: Verificações de integridade automatizadas garantem a confiabilidade de cada backup;
- Negativa: Custo recorrente do serviço de armazenamento em nuvem;
- Negativa: Necessidade de conexão de rede estável para a sincronização dos backups;
- Negativa: Complexidade adicional na configuração e manutenção da integração com serviços de nuvem.
"""


def _print_separator(title: str = "") -> None:
    print("\n" + "=" * 70)
    if title:
        print(title)
        print("=" * 70)


def _show_menu() -> str:
    _print_separator("SARC ADR Tools — Selecione uma ferramenta")
    print("  1 — Avaliador de Viabilidade de Melhorias Futuras (usa IA)")
    print("  2 — Gerador de Changelog de ADRs (diff sem IA)")
    print("  0 — Sair")
    print("=" * 70)
    return input("Opção: ").strip()


def _format_tools(tools) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        }
        for tool in tools
    ]


def _extract_tool_json(tool_result) -> dict:
    """MCP tool results arrive as a list of TextContent; parse the JSON text."""
    content = tool_result.content
    if isinstance(content, list) and content:
        text = getattr(content[0], "text", str(content[0]))
    else:
        text = str(content)
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {}


async def _run_viability_agent(ai_client: OpenAI, mcp_session, improvement: str) -> None:
    """Ferramenta 1: AI agent loop — a IA decide quando chamar a tool."""
    tools_list = await mcp_session.list_tools()
    formatted_tools = _format_tools(tools_list.tools)

    prompt = (
        f'Avalie a viabilidade da seguinte melhoria futura para o sistema SARC: "{improvement}"\n\n'
        "Utilize a ferramenta disponível e apresente um resumo indicando:\n"
        "- Quantas ADRs foram analisadas\n"
        "- Quais precisam ser revisadas (com justificativa)\n"
        "- Quais continuam válidas\n"
        "- Se novas ADRs são necessárias\n"
        "- Um resumo executivo do impacto geral"
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]

    generated_file = None

    while True:
        response = ai_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=formatted_tools,
            tool_choice="auto"
        )

        choice = response.choices[0]

        if choice.finish_reason == "stop":
            print(f"\n{choice.message.content}\n")
            if generated_file:
                print(f"📄 Relatório completo salvo em: {generated_file}\n")
            break

        elif choice.finish_reason == "tool_calls":
            messages.append(choice.message)

            for tool_call in choice.message.tool_calls:
                logger.info(f"Chamando ferramenta: {tool_call.function.name}")

                tool_result = await mcp_session.call_tool(
                    name=tool_call.function.name,
                    arguments=json.loads(tool_call.function.arguments)
                )

                parsed = _extract_tool_json(tool_result)
                if parsed.get("arquivo_gerado"):
                    generated_file = parsed["arquivo_gerado"]

                result_text = str(tool_result.content)
                logger.info(f"Resultado recebido ({len(result_text)} chars)")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": result_text
                })


async def _run_changelog_direct(mcp_session) -> None:
    """Ferramenta 2: chamada direta — sem IA, resultado puro do difflib."""
    print("\n[exemplo] comparando ADR-07 antes e depois da melhoria de backup em nuvem\n")
    logger.info("Chamando ferramenta: gerar_changelog_adr")

    result = await mcp_session.call_tool(
        name="gerar_changelog_adr",
        arguments={
            "old_version": OLD_ADR_EXAMPLE,
            "new_version": NEW_ADR_EXAMPLE,
        }
    )

    parsed = _extract_tool_json(result)
    print(f"\n{parsed.get('resumo', 'changelog gerado')}")
    print(f"  - Adições:      {parsed.get('mudancas_por_tipo', {}).get('adicao', 0)}")
    print(f"  - Remoções:     {parsed.get('mudancas_por_tipo', {}).get('remocao', 0)}")
    print(f"  - Modificações: {parsed.get('mudancas_por_tipo', {}).get('modificacao', 0)}")
    if parsed.get("arquivo_gerado"):
        print(f"\n📄 Changelog completo salvo em: {parsed['arquivo_gerado']}\n")


async def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    ai_client = OpenAI(api_key=api_key)

    params = session_parameters(command=sys.executable, args=["server.py"])

    async with stdio_client(params) as (read, write):
        async with session(read, write) as s:
            await s.initialize()

            while True:
                opcao = _show_menu()

                if opcao == "0":
                    print("\nEncerrando cliente. Até mais!\n")
                    break

                elif opcao == "1":
                    melhoria = input("\nDigite a melhoria futura a ser avaliada: ").strip()
                    if not melhoria:
                        print("Melhoria não pode ser vazia.")
                        continue
                    _print_separator("FERRAMENTA 1 — Avaliador de Viabilidade de Melhorias Futuras")
                    await _run_viability_agent(ai_client, s, melhoria)

                elif opcao == "2":
                    _print_separator("FERRAMENTA 2 — Gerador de Changelog de ADRs")
                    await _run_changelog_direct(s)

                else:
                    print("Opção inválida. Digite 1, 2 ou 0.")


if __name__ == "__main__":
    asyncio.run(main())
