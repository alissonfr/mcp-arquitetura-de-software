# SARC ADR Tools — Ferramentas MCP para Arquitetura de Software

Servidor MCP com duas ferramentas para análise e versionamento de Architecture Decision Records (ADRs) do sistema SARC (Sistema de Auxílio para Representantes Comerciais). Cada ferramenta gera um **relatório HTML estilizado** que é **aberto automaticamente no navegador**.

## Ferramentas Disponíveis

### 1. Avaliador de Viabilidade de Melhorias Futuras (`avaliar_viabilidade_melhoria`)

Recebe uma melhoria futura proposta (ex: "migrar para SPA com React") e o caminho do PDF do documento de arquitetura, e usa **IA** para analisar o impacto sobre cada ADR do SARC, indicando:

- Quais ADRs precisam ser revisadas
- Quais continuam válidas sem alteração
- Quais podem se tornar obsoletas
- Se novas ADRs precisam ser criadas para suportar a mudança

**Parâmetros:**
| Nome | Tipo | Descrição |
|------|------|-----------|
| `improvement` | `string` | Descrição da melhoria futura a ser avaliada |
| `pdf_path` | `string` | Caminho do PDF do documento de arquitetura |

**Exemplos de melhoria:** `"migrar para SPA com React"`, `"adicionar cache para relatórios"`, `"backup em nuvem"`

---

### 2. Gerador de Changelog de ADRs (`gerar_changelog_adr`)

Recebe os caminhos de **dois PDFs** do documento de arquitetura (versão antiga e versão nova), converte ambos para Markdown, casa as ADRs por identificador e gera um changelog visual com as diferenças por seção (Contexto, Decisão, Status, Consequências), classificando cada mudança como:

- 🟢 **adição**: conteúdo novo que não existia antes
- 🔴 **remoção**: conteúdo que foi removido
- 🟡 **modificação**: conteúdo que existia e foi alterado

Detecta ainda ADRs **adicionadas** ou **removidas** entre as duas versões. Esta ferramenta **não usa IA** — o diff é determinístico (biblioteca `difflib`).

**Parâmetros:**
| Nome | Tipo | Descrição |
|------|------|-----------|
| `old_pdf_path` | `string` | Caminho do PDF da versão antiga do documento |
| `new_pdf_path` | `string` | Caminho do PDF da versão nova do documento |

---

## Pré-requisitos

- Python 3.11 ou superior
- Chave de API da OpenAI (modelo `gpt-4.1-mini`) — necessária apenas para a Ferramenta 1
- PDF(s) do documento de arquitetura do SARC

## Instalação

**1. Crie e ative um ambiente virtual**

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python -m venv .venv
source .venv/bin/activate
```

**2. Instale as dependências**

```bash
pip install -r requirements.txt
```

**3. Configure as variáveis de ambiente**

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Abra o `.env` e preencha sua chave:

```
OPENAI_API_KEY=sk-...
```

**4. Adicione o(s) PDF(s) do documento de arquitetura**

Coloque o PDF na pasta `files/`:

```
files/documento_arquitetura_sarc.pdf
```

Para a Ferramenta 2, você precisa de **duas versões** do documento (ex.: `documento_arquitetura_sarc.pdf` e uma versão editada `documento_arquitetura_sarc_v2.pdf`).

## Uso

### Iniciar apenas o servidor MCP

```bash
python server.py
```

O servidor fica aguardando conexões de clientes MCP via stdin/stdout.

### Executar o cliente interativo

```bash
python client.py
```

O cliente exibe um menu para escolher a ferramenta:

```
  1 — Avaliador de Viabilidade de Melhorias Futuras (usa IA)
  2 — Gerador de Changelog de ADRs (diff sem IA)
  0 — Sair
```

- **Opção 1**: digite a melhoria e o caminho do PDF. Um agente de IA aciona a ferramenta MCP e resume o resultado no terminal; o relatório HTML abre no navegador.
- **Opção 2**: informe o caminho do PDF antigo e do PDF novo. O changelog é gerado e o HTML abre no navegador.

---

## Estrutura do Projeto

```
mcp-arquitetura-de-software/
├── core/
│   ├── adr_parser.py      # Extração de ADRs do markdown
│   ├── llm.py             # Cliente OpenAI e prompt da Ferramenta 1
│   ├── pdf_converter.py   # Conversão PDF → Markdown (markitdown)
│   ├── html_template.py   # Template HTML + CSS dos relatórios
│   └── report_writer.py   # Renderização e gravação dos relatórios HTML
├── tools/
│   ├── viability.py       # Orquestração da Ferramenta 1
│   └── changelog.py       # Orquestração da Ferramenta 2
├── files/
│   └── documento_arquitetura_sarc.pdf   ← coloque o(s) PDF(s) aqui
├── outputs/               # Relatórios .html gerados (criado automaticamente)
├── server.py              # Servidor MCP (FastMCP)
├── client.py              # Cliente MCP interativo
├── .env.example           # Template de configuração
└── requirements.txt       # Dependências
```

> As duas ferramentas gravam um relatório HTML em `outputs/`, abrem-no no navegador
> e retornam o caminho do arquivo. A Ferramenta 1 também retorna o JSON estruturado
> para o agente de IA resumir no terminal.

## Relação com as ADRs do SARC

| Ferramenta | Relação com as ADRs |
|------------|---------------------|
| **Avaliador de Viabilidade** | Lê todas as ADRs do documento de arquitetura e avalia o impacto de cada melhoria futura listada no documento, apoiando a decisão sobre quais ADRs revisitar |
| **Gerador de Changelog** | Compara duas versões do documento e rastreia a evolução das ADRs ao longo do tempo, facilitando a auditoria das mudanças nas decisões arquiteturais |
