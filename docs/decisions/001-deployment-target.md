# 001: Deploy to one server with Docker Compose

- **Status:** accepted, 2026-10-17
- **Evidence:** design constraint

## Context

The project must be deployable and defensible in an interview: a public URL and
concrete answers about containers, secrets, costs and the index build. It has few
users and a fixed corpus, and is run by one person on a small budget.

## Options

| Option | For | Against |
|---|---|---|
| A. Local only | simplest; no hosting cost | deployment questions stay hypothetical; nothing to show |
| **B. One server, Docker Compose** | real deployment and public URL; cheap; every operational question gets a concrete answer | single point of failure; scaling only on paper |
| C. Production scale (autoscaling, managed services, CI/CD) | high availability | far more infrastructure than the project needs; costly |

## Decision

Deploy all services as containers with Docker Compose on one cloud server. The
design names how each part would scale, without building it.

## Consequences

- Every service needs a container image and configuration from environment variables.
- Secrets live on the server only, never in images or the repository.
- The index is built by a separate job and shipped to the server, not built at startup.
- One server is a single point of failure; acceptable for a demo, stated as a risk.
- The server must fit the API (with the embedding model), Qdrant and the UI in memory.

## Open

- Which hosting provider and server size.

## How it will be validated

Deploy, then run the eval against the deployed URL and compare with local results.
