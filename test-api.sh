#!/usr/bin/env bash

set -euo pipefail

# Load env from project root if present
if [ -f ".env" ]; then
  echo "Loading .env"
  set -a
  # shellcheck disable=SC1091
  source ./.env
  set +a
fi

CLIENT_ID="${COGNITO_APP_CLIENT_ID:-}" 
if [ -z "${CLIENT_ID}" ]; then
  echo "Warning: COGNITO_APP_CLIENT_ID is not set; set it in .env to construct login URL"
fi

# Determine base URL
if [ "${LOCAL_DEV:-false}" = "true" ] || [ -z "${BASE_URL:-}" ]; then
  BASE="http://localhost:8000"
else
  BASE="${BASE_URL}"
fi

API_URL="${BASE}/api"

echo ""
echo "Root endpoint: "
curl -s -X GET "${API_URL%/}/.." | jq . || curl -X GET "${API_URL%/}/.."

# Build Cognito Hosted UI login URL if possible
if [ -n "${CLIENT_ID}" ] && [ -n "${COGNITO_DOMAIN_URL:-}" ]; then
  REDIRECT_URI="${BASE}/auth/callback"
  # URL-encode redirect_uri via python
  if command -v python3 >/dev/null 2>&1; then
    REDIRECT_URI_ENC=$(python3 - <<PY
import urllib.parse, os
print(urllib.parse.quote(os.environ['REDIRECT_URI'], safe=''))
PY
)
  else
    REDIRECT_URI_ENC="${REDIRECT_URI}"
  fi
  LOGIN_URL="${COGNITO_DOMAIN_URL%/}/login?client_id=${CLIENT_ID}&response_type=code&scope=email+openid+profile&redirect_uri=${REDIRECT_URI_ENC}"
  echo ""
  echo "Login URL: ${LOGIN_URL}"
fi

# ACCESS_TOKEN should be exported in the environment for protected endpoints
if [ -z "${ACCESS_TOKEN:-}" ]; then
  echo "Note: ACCESS_TOKEN not set; protected endpoints will fail with 401"
fi

# Example calls
curl -s -X GET "${API_URL}/user" -H "Authorization: Bearer ${ACCESS_TOKEN:-}" | jq . || true
curl -s -X GET "${API_URL}/fireflies/oyp-paoq-sty" -H "Authorization: Bearer ${ACCESS_TOKEN:-}" | jq . || true
curl -s -X GET "${API_URL}/analyze/oyp-paoq-sty" -H "Authorization: Bearer ${ACCESS_TOKEN:-}" | jq . || true

# Run analyzer helper (requires ACCESS_TOKEN)
uv run python analyzer.py ./transcripts/agenda.json ./transcripts/transcript.json --api-url "${BASE}"

# Webhook signature example (requires FIREFLIES_WEBHOOK_SECRET)
if [ -n "${FIREFLIES_WEBHOOK_SECRET:-}" ]; then
  curl -X POST -H "x-hub-signature: sha256=${FIREFLIES_WEBHOOK_SECRET}" "${API_URL}/webhooks/fireflies"
fi
