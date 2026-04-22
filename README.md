# Odoo AI Intelligence

AI assistant framework for Odoo 18 with:
- provider abstraction,
- tool-driven orchestration,
- Discuss bot integration,
- pluggable domain tool modules.

## Modules

- `m_ai_core`: provider config, orchestrator, generic read tools, debug/natural-response settings.
- `m_ai_openai`: OpenAI/OpenRouter provider implementation.
- `m_ai_tool_sale`: sale-domain tool policy extension (`sale.order` allowlist).
- `m_ai_discuss`: native Discuss integration (`AI Assistant` bot).
- `m_ai_chat`: optional legacy UI wrapper (delegates to core orchestrator).
- `m_ai_base`: deprecated compatibility shim.

## Documentation

- Usage and setup: `USAGE.md`
- Change history: `CHANGELOG.md`
