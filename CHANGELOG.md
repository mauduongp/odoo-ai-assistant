# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added
- `m_ai_core` module as the central AI runtime:
  - provider abstraction and configuration.
  - orchestrator service for tool-driven execution.
  - generic read tools (`query_records`, `read_records`).
- `m_ai_tool_sale` module:
  - sale-domain allowlist and policy extension for AI tools.
  - sales prompt guidance for better tool selection.
- `m_ai_discuss` module for native Discuss integration:
  - AI Assistant bot identity.
  - direct-chat and `/ai` channel trigger behavior.
- AI settings:
  - `AI Debug Mode`.
  - `AI Natural Response Mode`.
- Root `README.md` with architecture, setup, and troubleshooting notes.
- Docker/CI infra:
  - `Dockerfile`, `docker-compose.yml`, `.dockerignore`.
  - GitHub workflow: `.github/workflows/odoo-ci.yml`.
  - `scripts/ci-test.sh` and `requirements.txt`.

### Changed
- Refactored architecture to separate concerns:
  - `m_ai_base` converted to deprecated compatibility shim.
  - runtime logic moved toward `m_ai_core`.
  - discuss flow now calls core orchestrator service.
- Enabled two-step natural answer generation:
  - first step: structured tool/action selection.
  - second step: final user-facing answer generated from trusted tool output.
- Improved final-answer sanitization:
  - extracts text message when models output mixed JSON blocks.
- Improved reliability of Discuss reply posting:
  - retry logic for PostgreSQL serialization conflicts (`concurrent update`).
- Improved tool input robustness:
  - tolerant parsing for `ids` argument forms.
  - defensive serialization for varying many2one value shapes.
- Migrated project runtime defaults from Odoo 18 to Odoo 19:
  - Docker image/build defaults updated to `19.0`.
  - docs updated for Odoo 19 setup and usage.
- Updated sale tool dependency to `sale_management` for Odoo 19 compatibility.

### Fixed
- Multiple response quality issues:
  - reduced repetitive/robotic phrasing.
  - prevented raw tool JSON leakage to end users.
- Discuss no-response scenarios caused by module dependency and runtime edge cases.
- Failures caused by strict or brittle tool argument/value handling.
- Odoo 19 data loading error on bot user provisioning:
  - replaced invalid `groups_id` with `group_ids` in `m_ai_discuss` data.

## [2026-04-22]

### Commits
- `c8564bf`: add docker and ci infrastructure for local and github testing
- `67afb98`: update gitignore for local odoo source directory
- `52daa33`: improve natural ai responses and discuss reliability
- `bc0bddb`: add sale tool module and ai debug mode improvements
- `b1c6637`: refactor ai architecture into core orchestrator and generic tools
- `b243395`: add discuss AI assistant bot integration
- `55d1ce7`: add gitignore for python and local artifacts
- `6d82425`: add phase-1 Odoo AI chat assistant with SO status action
