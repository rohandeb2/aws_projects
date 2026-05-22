# Project 4 — Production Container Platform on AWS ECS Fargate

![AWS](https://img.shields.io/badge/AWS-ECS%20Fargate-orange?logo=amazon-aws) ![Docker](https://img.shields.io/badge/Docker-Container-blue?logo=docker) ![Region](https://img.shields.io/badge/Region-ap--south--1-yellow)

A production-grade container platform that deploys a Dockerized Flask application to AWS ECS Fargate with separate staging and production environments, runtime secret injection, auto scaling, and full observability via CloudWatch.

---

## Architecture Overview

<div align="center">
  <img src="img/Screenshot 2026-05-22 130602.png" >
</div>

## Tech Stack

| Service | Purpose |
|---|---|
| **Docker** | Package the Flask app into a container image |
| **Amazon ECR** | Private registry — stores versioned Docker images |
| **ECS Fargate** | Serverless container runtime — no EC2 to manage |
| **Task Definition** | Blueprint: image, CPU, memory, env vars, secrets |
| **ECS Service** | Keeps N tasks running, rolling deploys, self-healing |
| **Application Load Balancer** | Single entry point — port 80 (prod), port 8080 (staging) |
| **Secrets Manager** | DB credentials injected at runtime, never in the image |
| **CloudWatch Logs** | All container stdout/stderr captured automatically |
| **Container Insights** | Per-container CPU, memory, network metrics |
| **ECS Auto Scaling** | Scales 2 → 6 tasks when average CPU > 70% |

---

## Application

The Flask app (`app.py`) exposes a single route at `/` that displays:

- Container hostname — proves ALB is load balancing across multiple tasks on refresh
- Active environment (`staging` or `production`) — injected via env var
- DB username from Secrets Manager — proves runtime secret injection works

---

## Environments

| Environment | ALB Port | Tasks | CPU | Memory |
|---|---|---|---|---|
| Staging | 8080 | 1 (fixed) | 0.25 vCPU | 0.5 GB |
| Production | 80 | 2–6 (auto-scales) | 0.5 vCPU | 1 GB |

---

## Key Features Demonstrated

**Two-environment setup on one ALB** — staging and production share a single load balancer using separate listeners and target groups. Staging is always deployed first.

**Zero-downtime rolling deploys** — ECS replaces tasks one at a time. Old tasks stay alive until new ones pass health checks.

**Self-healing** — if a container crashes, the ECS service detects it and launches a replacement within 60 seconds. No manual action required.

**Secrets at runtime, never in the image** — DB credentials live exclusively in Secrets Manager and are injected as environment variables when each container starts. The image itself contains no sensitive data.

**CPU-based auto scaling** — the production service scales out when average CPU exceeds 70% and scales in after a cooldown period. No manual capacity management.

**Full observability without SSH** — all container output streams to CloudWatch log groups. Container Insights provides per-task CPU, memory, and network metrics.

---

## Secrets Managed

| Secret name | Key | Injected as |
|---|---|---|
| `devops/project4/db-credentials` | `username` | `DB_USER` |
| `devops/project4/db-credentials` | `password` | `DB_PASS` |
| `devops/project4/app-config` | `APP_ENV` | `APP_ENV` |

---

## Deployment Workflow

```bash
# 1. Authenticate Docker with ECR
aws ecr get-login-password --region ap-south-1 \
  | docker login --username AWS --password-stdin <ECR_URI>

# 2. Build and tag
docker build -t devops-project4/app .
docker tag devops-project4/app:latest <ECR_URI>:latest
docker tag devops-project4/app:latest <ECR_URI>:v1

# 3. Push
docker push <ECR_URI>:latest
docker push <ECR_URI>:v1

# 4. Deploy to staging first
aws ecs update-service --cluster devops-project4-cluster \
  --service project4-staging-service --force-new-deployment --region ap-south-1

# 5. Verify staging, then deploy to production
aws ecs update-service --cluster devops-project4-cluster \
  --service project4-production-service --force-new-deployment --region ap-south-1
```

**Rollback:** Update the task definition to reference an older image tag (e.g. `:v1`) and force a new deployment. Takes under 2 minutes.

---

## Verification Tests

| Test | What to check |
|---|---|
| Both environments reachable | `http://<ALB_DNS>` (prod) and `http://<ALB_DNS>:8080` (staging) load the app with correct `APP_ENV` labels |
| Load balancing | Refresh production URL 5–6 times — different container hostnames appear |
| Self-healing | Stop a running task in ECS console — replacement launches within 60 seconds |
| Secrets never in image | ECR scan results show no password; image filesystem contains no secret files |
| Logs in CloudWatch | `/ecs/project4-production` log group contains Flask startup and request logs |
| Container Insights | CloudWatch → Container Insights shows per-task CPU, memory, network metrics |

---

## Cost Estimate

| Resource | Cost |
|---|---|
| ECS Fargate (3 tasks) | ~$0.70/day |
| Application Load Balancer | ~$0.50/day |
| NAT Gateway | ~$1.00/day |
| ECR storage | negligible |
| **Total** | **~$2.00/day** |

> Delete all resources the same day to avoid ongoing charges.

---

## Prerequisites

- Docker Desktop installed and running
- AWS CLI configured (`aws configure`)
- AWS account with admin access
- Project 2 VPC (`devops-project2-vpc`) already exists with public + private subnets

---
## Proof of work:

<div align="center">
  <img src="img/Screenshot 2026-05-12 135506.png" >
</div>

<div align="center">
  <img src="img/Screenshot 2026-05-12 134934.png" >
</div>
