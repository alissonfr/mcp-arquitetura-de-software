# SARC ADR Tools — Ferramentas MCP para Arquitetura de Software

Servidor MCP com duas ferramentas de inteligência artificial para análise e versionamento de Architecture Decision Records (ADRs) do sistema SARC (Sistema de Análise de Requisitos e Contratos).

## Ferramentas Disponíveis

### 1. Avaliador de Viabilidade de Melhorias Futuras (`avaliar_viabilidade_melhoria`)

Recebe uma melhoria futura proposta (ex: "migrar para SPA com React") e usa IA para analisar o impacto sobre cada ADR do documento de arquitetura do SARC, indicando:

- Quais ADRs precisam ser revisadas
- Quais continuam válidas sem alteração
- Quais podem se tornar obsoletas
- Se novas ADRs precisam ser criadas para suportar a mudança

**Parâmetro:**
| Nome | Tipo | Descrição |
|------|------|-----------|
| `improvement` | `string` | Descrição da melhoria futura a ser avaliada |

**Exemplos de uso:**
- `"migrar para SPA com React"`
- `"adicionar cache para relatórios"`
- `"backup em nuvem"`

---

### 2. Gerador de Changelog de ADRs (`gerar_changelog_adr`)

Recebe duas versões de um ADR (texto antigo e texto novo) e gera um changelog estruturado com as diferenças por seção (Contexto, Decisão, Status, Consequências), classificando cada mudança como:

- **adição**: conteúdo novo que não existia antes
- **remoção**: conteúdo que foi removido
- **modificação**: conteúdo que existia e foi alterado

**Parâmetros:**
| Nome | Tipo | Descrição |
|------|------|-----------|
| `old_version` | `string` | Texto completo da versão antiga do ADR |
| `new_version` | `string` | Texto completo da versão nova do ADR |

---

## Pré-requisitos

- Python 3.11 ou superior
- Chave de API da OpenAI (modelo `gpt-4.1-mini`)
- PDF do documento de arquitetura do SARC

## Instalação

**1. Clone ou baixe o projeto**

**2. Crie e ative um ambiente virtual**

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python -m venv .venv
source .venv/bin/activate
```

**3. Instale as dependências**

```bash
pip install -r requirements.txt
```

**4. Configure as variáveis de ambiente**

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Abra o arquivo `.env` e preencha sua chave:

```
OPENAI_API_KEY=sk-...
```

**5. Adicione o PDF do documento de arquitetura**

Coloque o arquivo PDF na pasta `files/`:

```
files/documento_arquitetura_sarc.pdf
```

## Uso

### Iniciar apenas o servidor MCP

```bash
python server.py
```

O servidor ficará aguardando conexões de clientes MCP via stdin/stdout.

### Executar o cliente de demonstração

O cliente executa automaticamente as duas ferramentas com exemplos pré-configurados:

```bash
python client.py
```

O cliente irá:
1. Conectar ao servidor MCP via subprocess
2. Executar a **Ferramenta 1** avaliando a melhoria "adicionar cache para relatórios"
3. Executar a **Ferramenta 2** gerando o changelog entre duas versões da ADR-03

---

## Estrutura do Projeto

```
mcp-arquitetura-de-software/
├── core/
│   ├── adr_parser.py      # Extração de ADRs do markdown
│   ├── llm.py             # Cliente OpenAI e funções de prompt
│   ├── pdf_converter.py   # Conversão PDF → Markdown (markitdown)
│   └── report_writer.py   # Geração dos relatórios .md em outputs/
├── tools/
│   ├── viability.py       # Orquestração da Ferramenta 1
│   └── changelog.py       # Orquestração da Ferramenta 2
├── files/
│   └── documento_arquitetura_sarc.pdf   ← coloque o PDF aqui
├── outputs/               # Relatórios .md gerados (criado automaticamente)
├── server.py              # Servidor MCP (FastMCP)
├── client.py              # Cliente MCP de demonstração
├── .env.example           # Template de configuração
└── requirements.txt       # Dependências
```

> As duas ferramentas gravam um relatório formatado em `outputs/` (um `.md` por
> execução) e retornam o caminho do arquivo. A Ferramenta 1 também retorna o JSON
> estruturado para o agente de IA resumir no terminal.

## Relação com as ADRs do SARC

| Ferramenta | Relação com as ADRs |
|------------|---------------------|
| **Avaliador de Viabilidade** | Lê todas as ADRs do documento de arquitetura e avalia o impacto de cada melhoria futura listada no documento, apoiando a tomada de decisão sobre quais ADRs revisitar |
| **Gerador de Changelog** | Rastreia a evolução de ADRs individuais ao longo do tempo, facilitando a auditoria de mudanças nas decisões arquiteturais |
