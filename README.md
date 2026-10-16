# shortlink-platform

A URL shortener built as an end-to-end DevOps project: the app is small on purpose, and the focus is the delivery pipeline around it.

| Tool | What it does here |
|------|-------------------|
| **Docker** | Multi-stage, non-root image; Compose stack with Redis, Prometheus and Grafana |
| **Kubernetes** | Kustomize base + dev overlay: probes, rolling updates, HPA, resource limits, hardened security context, NetworkPolicy (only the app can reach Redis) |
| **GitHub Actions** | Test, build, Trivy scan, push to GHCR, then deploy to a throwaway `kind` cluster and smoke test it |
| **Terraform** | ECR repository (immutable tags, scan on push, lifecycle policy) and a GitHub OIDC role so CI needs no stored AWS keys |

## Architecture

```
git push -> GitHub Actions -> pytest -> docker build -> Trivy scan -> GHCR
                                                                       |
                                          kind cluster <- kustomize <--+
                                          (deploy + smoke test)

Terraform -> ECR + IAM OIDC role (for pushing to AWS ECR from CI)
```

## Run locally

```bash
make up          # app :8080, Prometheus :9090, Grafana :3000
curl -X POST localhost:8080/api/shorten -H 'content-type: application/json' \
     -d '{"url":"https://example.com"}'
curl -i localhost:8080/<code>
```

## Run on Kubernetes

```bash
kind create cluster
make k8s-up
kubectl -n shortlink port-forward svc/shortlink 8080:80
```

## Terraform

```bash
cd terraform
terraform init
terraform plan
```

Nothing is applied by CI; the workflow only runs `fmt`, `validate` and `tfsec`.

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/shorten` | Body `{"url": "https://..."}`, returns `{code, short_url}` |
| GET | `/<code>` | 302 redirect |
| GET | `/healthz`, `/readyz` | Liveness and readiness (readiness checks Redis) |
| GET | `/metrics` | Prometheus metrics |

## Tests

```bash
make test
```
