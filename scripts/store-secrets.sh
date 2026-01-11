#!/bin/bash
# Store secrets in Google Cloud Secret Manager
#
# Run this ONCE to migrate existing secrets to Secret Manager.
# Requires: gcloud CLI authenticated with appropriate permissions
#
# Usage:
#   ./scripts/store-secrets.sh
#
# Prerequisites:
#   1. Enable Secret Manager API:
#      gcloud services enable secretmanager.googleapis.com
#
#   2. Ensure your account/service account has roles/secretmanager.admin

set -euo pipefail

PROJECT_ID="${PROJECT_ID:-lean-proof-checker}"

echo "Storing secrets in project: $PROJECT_ID"
echo "============================================"

# Helper function to create or update a secret
store_secret() {
    local name="$1"
    local value="$2"

    if gcloud secrets describe "$name" --project="$PROJECT_ID" &>/dev/null; then
        echo "Updating secret: $name"
        echo -n "$value" | gcloud secrets versions add "$name" --data-file=- --project="$PROJECT_ID"
    else
        echo "Creating secret: $name"
        echo -n "$value" | gcloud secrets create "$name" --data-file=- --project="$PROJECT_ID"
    fi
}

# Prompt for each secret value
echo ""
echo "Enter the secret values (or press Enter to skip):"
echo ""

read -sp "CL_POSTGRES_PASSWORD: " CL_POSTGRES_PASSWORD
echo ""
read -sp "THEOREM_POSTGRES_PASSWORD: " THEOREM_POSTGRES_PASSWORD
echo ""
read -p "CONTRACT_ADDRESS: " CONTRACT_ADDRESS
read -sp "HTTP_PROVIDER (Infura/Alchemy URL): " HTTP_PROVIDER
echo ""
read -p "ADMIN_EMAIL: " ADMIN_EMAIL
read -p "SENDER_EMAIL: " SENDER_EMAIL
read -p "AWS_REGION [eu-north-1]: " AWS_REGION
AWS_REGION="${AWS_REGION:-eu-north-1}"
read -sp "AWS_ACCESS_KEY_ID: " AWS_ACCESS_KEY_ID
echo ""
read -sp "AWS_SECRET_ACCESS_KEY: " AWS_SECRET_ACCESS_KEY
echo ""
read -sp "CHAINLINK_KEYSTORE_PASSWORD: " CHAINLINK_KEYSTORE_PASSWORD
echo ""
read -sp "INFURA_PROJECT_ID (for Chainlink node): " INFURA_PROJECT_ID
echo ""

echo ""
echo "Storing secrets..."
echo ""

# Store each secret
[ -n "$CL_POSTGRES_PASSWORD" ] && store_secret "theorem-cl-postgres-password" "$CL_POSTGRES_PASSWORD"
[ -n "$THEOREM_POSTGRES_PASSWORD" ] && store_secret "theorem-postgres-password" "$THEOREM_POSTGRES_PASSWORD"
[ -n "$CONTRACT_ADDRESS" ] && store_secret "theorem-contract-address" "$CONTRACT_ADDRESS"
[ -n "$HTTP_PROVIDER" ] && store_secret "theorem-http-provider" "$HTTP_PROVIDER"
[ -n "$ADMIN_EMAIL" ] && store_secret "theorem-admin-email" "$ADMIN_EMAIL"
[ -n "$SENDER_EMAIL" ] && store_secret "theorem-sender-email" "$SENDER_EMAIL"
[ -n "$AWS_REGION" ] && store_secret "theorem-aws-region" "$AWS_REGION"
[ -n "$AWS_ACCESS_KEY_ID" ] && store_secret "theorem-aws-access-key-id" "$AWS_ACCESS_KEY_ID"
[ -n "$AWS_SECRET_ACCESS_KEY" ] && store_secret "theorem-aws-secret-access-key" "$AWS_SECRET_ACCESS_KEY"
[ -n "$CHAINLINK_KEYSTORE_PASSWORD" ] && store_secret "theorem-chainlink-keystore-password" "$CHAINLINK_KEYSTORE_PASSWORD"
[ -n "$INFURA_PROJECT_ID" ] && store_secret "theorem-infura-project-id" "$INFURA_PROJECT_ID"

echo ""
echo "Done! Secrets stored in project: $PROJECT_ID"
echo ""
echo "Next steps:"
echo "  1. Grant the VM's service account access to these secrets:"
echo "     gcloud secrets add-iam-policy-binding theorem-postgres-password \\"
echo "       --member='serviceAccount:YOUR-SA@PROJECT.iam.gserviceaccount.com' \\"
echo "       --role='roles/secretmanager.secretAccessor'"
echo ""
echo "  2. Set the VM startup script to use scripts/vm-startup.sh"
