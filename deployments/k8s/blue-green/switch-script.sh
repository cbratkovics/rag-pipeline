#!/bin/bash

# Blue-Green Deployment Switch Script for RAG Pipeline
# Usage: ./switch-script.sh [blue|green]

set -e

TARGET_VERSION=${1:-green}
NAMESPACE=${2:-rag-production}

if [[ "$TARGET_VERSION" != "blue" && "$TARGET_VERSION" != "green" ]]; then
    echo "Error: Invalid version. Use 'blue' or 'green'"
    exit 1
fi

echo "Switching RAG API to $TARGET_VERSION version in namespace $NAMESPACE"

# Update the main service to point to the target version
kubectl patch service rag-api -n $NAMESPACE -p \
  '{"spec":{"selector":{"app":"rag-api","version":"'$TARGET_VERSION'"}}}'

echo "Service switched to $TARGET_VERSION"

# Wait for the new pods to be ready
echo "Waiting for $TARGET_VERSION pods to be ready..."
kubectl wait --for=condition=ready pod \
  -l app=rag-api,version=$TARGET_VERSION \
  -n $NAMESPACE \
  --timeout=300s

echo "Switch complete! RAG API is now serving from $TARGET_VERSION"

# Show the current status
echo ""
echo "Current deployment status:"
kubectl get deployments -n $NAMESPACE -l app=rag-api
echo ""
echo "Current pods:"
kubectl get pods -n $NAMESPACE -l app=rag-api
echo ""
echo "Service endpoints:"
kubectl get endpoints rag-api -n $NAMESPACE