#!/usr/bin/env bash
set -euo pipefail
random_string() {
  LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 64
}
cat > .env <<EOT
GRAFANA_ADMIN_PASSWORD=$(random_string)
N8N_USER=admin
N8N_PASS=$(random_string)
MEILI_MASTER_KEY=$(random_string)
QDRANT_API_KEY=$(random_string)
NEXTAUTH_SECRET=$(random_string)
LANGFUSE_SALT=$(random_string)
WORDPRESS_JWT_AUTH_SECRET_KEY=$(random_string)
EOT
