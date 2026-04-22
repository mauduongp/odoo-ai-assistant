# Odoo AI Intelligence

AI assistant modules for Odoo 18 with provider abstraction, Discuss integration, and pluggable domain tools.

## Modules

- `m_ai_core`: provider config, orchestrator, generic read tools, debug mode.
- `m_ai_openai`: OpenAI/OpenRouter provider implementation.
- `m_ai_tool_sale`: sale-domain allowlist and human formatting for `sale.order`.
- `m_ai_discuss`: native Discuss bot integration (`AI Assistant` user/partner).
- `m_ai_chat`: optional legacy UI wrapper (delegates to core orchestrator).
- `m_ai_base`: deprecated compatibility shim.

## Install / Upgrade Order

1. `m_ai_core`
2. `m_ai_tool_sale`
3. `m_ai_openai`
4. `m_ai_chat` (optional)
5. `m_ai_discuss`
6. `m_ai_base` (compatibility)

After upgrade, restart Odoo server.

## Basic Usage

- Configure provider in `Settings > AI`:
  - AI Provider
  - API key / base URL
  - default model
- Open Discuss:
  - direct chat with `AI Assistant`: plain message
  - channel message: prefix with `/ai`

## Debug Mode

Enable `Settings > AI > AI Debug Mode` during testing.

When enabled:
- orchestrator logs prompt/envelope/tool arguments/results.
- Discuss replies include detailed error text.

When disabled:
- users receive safe generic errors.
- stack traces remain in server logs only.

## Known Benign Log Pattern

You may see:

`ERROR: could not serialize access due to concurrent update`

This is common in Discuss concurrent updates (typing/read markers). Odoo retries these transactions automatically. If AI replies still succeed, this is usually not a functional issue.

Investigate only if:
- retries are exhausted,
- users see repeated failures,
- latency is consistently high.
