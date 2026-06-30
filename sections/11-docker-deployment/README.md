# Section 11 · Docker, Deployment, and Making It Real

**Estimated runtime:** 1h 45m · **Fast-track:** ✅ Yes · **Phase:** 🔴 Deployment & Capstone

Containerizes the FastAPI service from Section 8, sets up environment variable management properly (never in code), and gets a CI/CD pipeline running — the last piece before Section 12 deploys the full five-agent system.

## Lectures

| # | Title | Duration |
|---|---|---|
| 11.1 | Docker for AI engineers: images, containers, compose stacks | 16 min |
| 11.2 | Containerising your FastAPI agent service | 12 min |
| 11.3 | Environment variable management: `.env` files, secrets, never in code | 8 min |
| 11.4 | Railway.app deployment: push to cloud in 15 minutes (zero cost) | 14 min |
| 11.5 | GitHub Actions: CI/CD pipeline for your agent — test, build, deploy | 16 min |
| 11.6 | Production upgrade path: ECS Fargate, Kubernetes — what scales and when | 10 min |
| 11.Q | Quiz: Deployment (6 questions) | — |

## Files in this folder

```
11-docker-deployment/
├── README.md
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## Where this code goes next

This `Dockerfile` and CI workflow become the root-level `Dockerfile` and `.github/workflows/ci.yml` for the full capstone in Section 12.
