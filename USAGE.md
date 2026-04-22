# Usage Guide

This guide explains how to run and use the Odoo AI assistant project in a new environment.

## 1) Prerequisites

- Docker and Docker Compose
- Odoo 19-compatible environment
- OpenAI/OpenRouter API key (or compatible provider key)
- Optional but recommended: local Odoo 19 source addons (`odoo_src`) for reference during development/debugging

## 2) Start the stack

From project root:

```bash
docker compose up -d
```

Optional: restart web container after code changes:

```bash
docker restart odoo-ai-intelligence-web-1
```

## 3) Install modules (important order)

In Odoo Apps, install/upgrade in this order:

1. `m_ai_core`
2. `m_ai_tool_sale`
3. `m_ai_openai`
4. `m_ai_chat` (optional legacy UI)
5. `m_ai_discuss`
6. `m_ai_base` (deprecated compatibility shim)

After module upgrades, restart Odoo server if Python code changed.

## 4) Configure AI provider

Go to `Settings > AI`:

- Set `AI Provider`
- Configure API key (and base URL if needed)
- Set default model
- Use `Test Connection`

## 5) Choose runtime behavior

In `Settings > AI`:

- `AI Natural Response Mode`:
  - ON: LLM generates final human-style answer from tool results
  - OFF: backend returns deterministic fallback text
- `AI Debug Mode`:
  - ON: detailed AI logs and verbose error replies for testing
  - OFF: safer production behavior

## 6) Use in Discuss

### Direct chat with AI Assistant

- Open Discuss
- Start/open direct chat with `AI Assistant`
- Send natural questions, for example:
  - `What is status of SO00002?`
  - `List ongoing sale orders`
  - `List orders with amount at least 100`

### Channel usage

- In channels, prefix with `/ai`:
  - `/ai list sale orders above 100`

## 7) What the assistant can do now

- Read-only sale order queries through safe tools:
  - `query_records`
  - `read_records`
- Human-style final responses (when natural mode is ON)
- Respect Odoo access rights/rules via user context

## 8) Run tests

Run CI-like test pass locally:

```bash
ODOO_MODULES="m_ai_core,m_ai_tool_sale,m_ai_openai,m_ai_chat,m_ai_discuss,m_ai_base" \
ODOO_TEST_TAGS="/m_ai_core,/m_ai_tool_sale,/m_ai_chat,/m_ai_discuss,/m_ai_base" \
./scripts/ci-test.sh
```

## 9) Troubleshooting

### No AI reply in chat

- Ensure `m_ai_discuss` and `m_ai_tool_sale` are installed
- Restart Odoo after upgrades
- Check provider config and test connection

### Raw JSON appears in reply

- Ensure latest `m_ai_core` is installed (includes final-answer sanitization)
- Keep `AI Natural Response Mode` ON for best UX

### `Fields are not allowed for model ...`

- Tool requested a field not in allowlist
- Extend allowlist in domain tool module (for sales: `m_ai_tool_sale`)

### `could not serialize access due to concurrent update`

- Common Discuss concurrency behavior
- Retry handling is implemented in Discuss reply posting
- If intermittent and replies still succeed, usually benign

## 10) Architecture at a glance

- `m_ai_core`: provider + orchestrator + generic tool engine
- `m_ai_tool_sale`: sale model policy/allowlist and sales prompt hints
- `m_ai_openai`: provider backend implementation
- `m_ai_discuss`: Discuss transport adapter (bot input/output)
- `m_ai_chat`: optional legacy wrapper UI
- `m_ai_base`: deprecated compatibility module
