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
DEFAULT_PDF = "files/documento_arquitetura_sarc.pdf"

SYSTEM_PROMPT = """
Você é um assistente especializado em arquitetura de software com acesso às ferramentas
MCP do sistema SARC (Sistema de Auxílio para Representantes Comerciais).

Quando solicitado, utilize as ferramentas disponíveis para analisar o impacto de
melhorias futuras sobre as ADRs existentes do sistema SARC, apresentando os resultados
de forma clara e organizada.
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


def _ask_path(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or (default or "")


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


async def _run_viability_agent(ai_client: OpenAI, mcp_session, improvement: str, pdf_path: str) -> None:
    """Ferramenta 1: AI agent loop — a IA decide quando chamar a tool."""
    tools_list = await mcp_session.list_tools()
    formatted_tools = _format_tools(tools_list.tools)

    prompt = (
        f'Avalie a viabilidade da seguinte melhoria futura para o sistema SARC: "{improvement}".\n'
        f'Use o documento de arquitetura localizado no caminho: "{pdf_path}".\n\n'
        "Chame a ferramenta de avaliação de viabilidade passando a melhoria e o caminho do PDF, "
        "e ao final apresente um resumo indicando:\n"
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
                print(f"📄 Relatório HTML aberto no navegador: {generated_file}\n")
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


async def _run_changelog_direct(mcp_session, old_pdf_path: str, new_pdf_path: str) -> None:
    """Ferramenta 2: chamada direta — sem IA, compara dois PDFs reais via difflib."""
    logger.info("Chamando ferramenta: gerar_changelog_adr")

    result = await mcp_session.call_tool(
        name="gerar_changelog_adr",
        arguments={
            "old_pdf_path": old_pdf_path,
            "new_pdf_path": new_pdf_path,
        }
    )

    parsed = _extract_tool_json(result)

    if parsed.get("erro"):
        print(f"\n⚠️  {parsed['erro']}\n{parsed.get('dica', '')}\n")
        return

    by_type = parsed.get("mudancas_por_tipo", {})
    print(f"\n{parsed.get('resumo', 'changelog gerado')}")
    print(f"  - Adições:      {by_type.get('adicao', 0)}")
    print(f"  - Remoções:     {by_type.get('remocao', 0)}")
    print(f"  - Modificações: {by_type.get('modificacao', 0)}")
    if parsed.get("arquivo_gerado"):
        print(f"\n📄 Changelog HTML aberto no navegador: {parsed['arquivo_gerado']}\n")


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
                    pdf_path = _ask_path("Caminho do PDF do documento de arquitetura", DEFAULT_PDF)
                    _print_separator("FERRAMENTA 1 — Avaliador de Viabilidade de Melhorias Futuras")
                    await _run_viability_agent(ai_client, s, melhoria, pdf_path)

                elif opcao == "2":
                    old_pdf = _ask_path("\nCaminho do PDF da versão ANTIGA", DEFAULT_PDF)
                    new_pdf = _ask_path("Caminho do PDF da versão NOVA")
                    if not new_pdf:
                        print("O caminho do PDF da versão nova é obrigatório.")
                        continue
                    _print_separator("FERRAMENTA 2 — Gerador de Changelog de ADRs")
                    await _run_changelog_direct(s, old_pdf, new_pdf)

                else:
                    print("Opção inválida. Digite 1, 2 ou 0.")


if __name__ == "__main__":
    asyncio.run(main())
