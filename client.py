from mcp.client.stdio import stdio_client
from mcp import ClientSession as session, StdioServerParameters as session_parameters
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
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
    print("  3 — Informações do servidor MCP")
    print("  0 — Sair")
    print("=" * 70)
    return input("Opção: ").strip()


def _ask_path(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    # Remove aspas e espaços que costumam vir junto ao colar caminhos no Windows
    value = input(f"{label}{suffix}: ").strip().strip('"').strip("'").strip()
    return value or (default or "")


def _clickable(path: str) -> str:
    # OSC 8 hyperlink: clicável em terminais modernos (VSCode, GNOME Terminal,
    # iTerm2, Windows Terminal). Onde não há suporte, mostra apenas o caminho.
    uri = Path(path).resolve().as_uri()
    return f"\033]8;;{uri}\033\\{path}\033]8;;\033\\"


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
    """Tool 1: AI agent loop — the AI decides when to call the tool."""
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
                print(f"📄 Relatório HTML (abre no navegador, ou clique aqui): {_clickable(generated_file)}\n")
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
    """Tool 2: direct call — no AI, compares two real PDFs via difflib."""
    logger.info("Chamando ferramenta: gerar_changelog_adr")

    result = await mcp_session.call_tool(
        name="gerar_changelog_adr",
        arguments={
            "old_pdf_path": old_pdf_path,
            "new_pdf_path": new_pdf_path,
        }
    )

    parsed = _extract_tool_json(result)

    if not parsed:
        print(f"\n⚠️  A ferramenta retornou um erro inesperado:\n{result.content}\n")
        return

    if parsed.get("erro"):
        print(f"\n⚠️  {parsed['erro']}\n{parsed.get('dica', '')}\n")
        return

    by_type = parsed.get("mudancas_por_tipo", {})
    print(f"\n{parsed.get('resumo', 'changelog gerado')}")
    print(f"  - Adições:      {by_type.get('adicao', 0)}")
    print(f"  - Remoções:     {by_type.get('remocao', 0)}")
    print(f"  - Modificações: {by_type.get('modificacao', 0)}")
    if parsed.get("arquivo_gerado"):
        print(f"\n📄 Changelog HTML (abre no navegador, ou clique aqui): {_clickable(parsed['arquivo_gerado'])}\n")


async def _run_server_info(mcp_session) -> None:
    """Tool 3: direct call — returns the MCP server information."""
    logger.info("Chamando ferramenta: informacoes_servidor")

    result = await mcp_session.call_tool(name="informacoes_servidor", arguments={})
    info = _extract_tool_json(result)

    print(f"\nNome:      {info.get('nome', '')}")
    print(f"Descrição: {info.get('descricao', '')}")
    print(f"Versão:    {info.get('versao', '')}")
    print("Ferramentas disponíveis:")
    for tool_name in info.get("ferramentas", []):
        print(f"  - {tool_name}")
    print()


async def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    ai_client = OpenAI(api_key=api_key)

    params = session_parameters(command=sys.executable, args=["server.py"])

    async with stdio_client(params) as (read, write):
        async with session(read, write) as s:
            await s.initialize()

            while True:
                option = _show_menu()

                if option == "0":
                    print("\nEncerrando cliente. Até mais!\n")
                    break

                elif option == "1":
                    improvement = input("\nDigite a melhoria futura a ser avaliada: ").strip()
                    if not improvement:
                        print("Melhoria não pode ser vazia.")
                        continue
                    pdf_path = _ask_path("Caminho do PDF do documento de arquitetura")
                    _print_separator("FERRAMENTA 1 — Avaliador de Viabilidade de Melhorias Futuras")
                    await _run_viability_agent(ai_client, s, improvement, pdf_path)

                elif option == "2":
                    old_pdf = _ask_path("\nCaminho do PDF da versão ANTIGA")
                    new_pdf = _ask_path("Caminho do PDF da versão NOVA")
                    if not new_pdf:
                        print("O caminho do PDF da versão nova é obrigatório.")
                        continue
                    _print_separator("FERRAMENTA 2 — Gerador de Changelog de ADRs")
                    await _run_changelog_direct(s, old_pdf, new_pdf)

                elif option == "3":
                    _print_separator("INFORMAÇÕES DO SERVIDOR MCP")
                    await _run_server_info(s)

                else:
                    print("Opção inválida. Digite 1, 2, 3 ou 0.")


if __name__ == "__main__":
    asyncio.run(main())
