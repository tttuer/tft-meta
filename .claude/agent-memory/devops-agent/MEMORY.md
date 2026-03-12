# DevOps Agent Memory

## Project Structure
- `k8s/`: Kubernetes manifests
- `scripts/`: Deployment automation scripts
- `contracts/api-spec.yaml`: Source of truth for ports, image names, env vars
- `contracts/flutter-build.md`: Flutter build artifact locations

## Critical Pre-Work
Before EVERY task:
1. Read `contracts/api-spec.yaml` for image names, ports, env vars
2. Read `contracts/flutter-build.md` for build artifact locations

## Namespace
ALL resources MUST be in `namespace: tft-meta`

## Required Labels
```yaml
labels:
  app: tft-meta
  managed-by: devops-agent
```

## Image Names
- ALWAYS use exact names from `contracts/api-spec.yaml`
- NEVER invent or modify image names

## Secrets Management
- NEVER hardcode secrets in manifests
- Provide kubectl commands for users to create secrets
- Use `secretKeyRef` to reference secrets in manifests

## Deployment Script (scripts/deploy.sh)
- Must be idempotent
- Deploy entire stack in one command
- Order: namespace → secrets docs → configmaps → deployments → services → ingress
- Include health check verification

## Directory Restrictions
- **ONLY** modify: `k8s/` and `scripts/`
- **NEVER** modify: `backend/`, `flutter_app/`, or other directories

## External Access
- Prefer Ingress for HTTP/HTTPS
- Document external URLs/IPs after deployment
- If using NodePort, document exposed ports
