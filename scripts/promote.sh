#!/usr/bin/env bash
# Audit 4.6 — Build once, deploy anywhere.
#
# Promotes a Docker image tag through dev → staging → prod
# by retagging it in the registry and triggering ArgoCD / Helm rollout.
#
# Usage:
#   ./scripts/promote.sh <image-name> <source-tag> <target-env>
#
# Example:
#   ./scripts/promote.sh backend abc1234 staging
#   ./scripts/promote.sh backend abc1234 prod

set -euo pipefail

REGISTRY="${REGISTRY:-ghcr.io/vaxgenesis}"
REPO="${REGISTRY}/$1"
SOURCE_TAG="$2"
TARGET_ENV="$3"  # dev | staging | prod

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Usage: $0 <image-name> <source-tag> <target-env>"
    echo "Example: $0 backend abc1234 staging"
    exit 1
fi

case "$TARGET_ENV" in
    dev)     ENV_TAG="dev-latest"     ;;
    staging) ENV_TAG="staging-latest" ;;
    prod)    ENV_TAG="prod-latest"    ;;
    *)
        echo "ERROR: target-env must be one of: dev, staging, prod"
        exit 1
        ;;
esac

echo "=== Promoting $REPO:$SOURCE_TAG → $REPO:$ENV_TAG ==="

# 1. Pull the source image (must already exist)
docker pull "$REPO:$SOURCE_TAG"

# 2. Retag with the environment alias
docker tag "$REPO:$SOURCE_TAG" "$REPO:$ENV_TAG"

# 3. Push the new tag
docker push "$REPO:$ENV_TAG"

# 4. Update the Helm values for the target environment
case "$TARGET_ENV" in
    staging)
        ENV_FILE="infra/helm/vaxgenesis/values-staging.yaml"
        ;;
    prod)
        ENV_FILE="infra/helm/vaxgenesis/values-prod.yaml"
        ;;
    *)
        ENV_FILE=""
        ;;
esac

if [ -n "$ENV_FILE" ] && [ -f "$ENV_FILE" ]; then
    # Update the image tag in the values file
    sed -i.bak "s|tag: \".*\"|tag: \"$SOURCE_TAG\"|g" "$ENV_FILE"
    rm -f "$ENV_FILE.bak"
    echo "Updated $ENV_FILE with tag $SOURCE_TAG"

    # Commit the change
    git add "$ENV_FILE"
    git commit -m "chore(deploy): promote $1 to $TARGET_ENV at $SOURCE_TAG"
    echo "Committed values update. Push to deploy."
fi

# 5. If ArgoCD is installed, sync the app
if command -v argocd >/dev/null 2>&1; then
    echo "Triggering ArgoCD sync..."
    argocd app sync "vaxgenesis-$TARGET_ENV" --force
fi

echo ""
echo "=== Promotion complete ==="
echo "Image: $REPO:$ENV_TAG (points to $SOURCE_TAG)"
echo "Helm values updated for $TARGET_ENV"
echo ""
echo "Next: push the values commit, then ArgoCD will auto-deploy."
