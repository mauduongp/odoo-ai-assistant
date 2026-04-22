#!/usr/bin/env bash
# Run the same Odoo install + test pass used in GitHub Actions (Runbot-style gate).
#
# By default only tests under your addons run (--test-tags), like a scoped addon job.
# For a full Odoo core test run (slow, Runbot-parity): ODOO_TEST_SCOPE=full ./scripts/ci-test.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-odoo-ai-ci}"
ODOO_TEST_DB="${ODOO_TEST_DB:-ci_test_$$}"
ODOO_MODULES="${ODOO_MODULES:-m_ai_base}"
ODOO_TEST_SCOPE="${ODOO_TEST_SCOPE:-addons}"

cleanup() {
  docker compose exec -T db psql -U odoo -d postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${ODOO_TEST_DB}' AND pid <> pg_backend_pid();" \
    >/dev/null 2>&1 || true
  docker compose exec -T db dropdb -U odoo --if-exists "${ODOO_TEST_DB}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

args=(
  -d "${ODOO_TEST_DB}"
  --db_host=db
  --db_user=odoo
  --db_password=odoo
  --without-demo=all
  --test-enable
  --stop-after-init
  -i "${ODOO_MODULES}"
  --log-level=test
)

if [ "${ODOO_TEST_SCOPE}" = "full" ]; then
  :
else
  tags="${ODOO_TEST_TAGS:-/m_ai_base}"
  args+=(--test-tags "${tags}")
fi

docker compose run --rm web odoo "${args[@]}"

echo "OK: Odoo tests finished for DB=${ODOO_TEST_DB} modules=${ODOO_MODULES} scope=${ODOO_TEST_SCOPE}"
