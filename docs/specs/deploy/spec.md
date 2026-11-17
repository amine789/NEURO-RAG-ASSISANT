# Deployment: spec

Roadmap row 7: the API runs on Kubernetes with a public URL, and the eval runs
against it.

## Goal

The row 5 API, with row 6's tracing, runs on a small Kubernetes cluster
(k3s on one VM) and answers at a public URL. Qdrant runs next to it with the
same 4,313 chunks as the laptop, kept on a disk that survives restarts. Keys
are never in git or in the image. The deployed index is checked against the
laptop's, and the eval is run against it.

## In and out

- **In:** the code at the commit being deployed, the laptop's Qdrant
  collection `papers` (4,313 chunks), and the keys in `.env`.
- **Out:** `http://<VM_IP>/ask` and `http://<VM_IP>/health`, answering exactly
  as on the laptop; one trace per request in Langfuse, as in row 6.

```
            internet
               │  :80
        ┌──────▼──────────────── VM (k3s) ───────────────────────────┐
        │  Traefik Ingress  ── rate limit (choice 8) ──►  Service api │
        │                                                   │         │
        │                         Deployment api (1 pod) ◄──┘         │
        │                         image: ghcr.io/.../neuro-rag-api    │
        │                         keys from Secret neuro-rag-keys     │
        │                               │ http://qdrant:6333          │
        │                         StatefulSet qdrant (1 pod)          │
        │                         volume: 2 GiB, local disk           │
        └─────────────────────────────────────────────────────────────┘
                 Claude API ◄── api ──► Langfuse Cloud
```

Qdrant has no public port: only the API reaches it, inside the cluster.

## Settings

| Setting | Value | Why |
|---|---|---|
| cluster | k3s, one node | one install command; full Kubernetes API; ~512 MB of RAM for itself |
| VM | Hetzner Cloud CX22: 2 vCPU, 4 GB RAM, 40 GB disk, x86, Ubuntu 24.04; about €5 a month (check the current price) | 4 GB holds k3s, Qdrant and the API with the two embedding models; a 4 GB droplet elsewhere is about $24 |
| image | `python:3.11-slim`; dependencies from `requirements.lock` (pinned), then the package with `pip install --no-deps .`; the two fastembed models downloaded at build time | the image runs the versions rows 1–6 were validated with (choice 12); the pod starts without downloading anything |
| image platform | `linux/amd64`, built on the Mac with `docker buildx build --platform linux/amd64` | the Mac is ARM, the VM is x86 |
| registry | GitHub Container Registry, `ghcr.io/amine789/neuro-rag-api`, public | free; the image holds no key; CD (later) pushes to the same place |
| image tag | the git commit's short hash, e.g. `c2e2703` | each deploy names exactly the code it runs; no `latest` |
| manifests | plain YAML in `deploy/k8s/`, applied with `kubectl apply -f deploy/k8s/` | no Helm or Kustomize for 3 files |
| Qdrant | `qdrant/qdrant:v1.19.1` (the laptop's version), a StatefulSet with a 2 GiB volume from k3s's built-in `local-path` storage | snapshots restore only into the same version; the volume survives pod restarts |
| index transfer | a Qdrant snapshot of `papers`, made on the laptop, uploaded through a port-forward | tens of MB, no PDFs or GROBID on the server |
| keys | a Secret `neuro-rag-keys`, created with `kubectl create secret generic --from-env-file=.env`; the Deployment reads it with `envFrom` | never in git or the image; `QDRANT_URL` in `.env` is overridden by the Deployment's own `env` (Kubernetes gives `env` precedence); every `.env` line must be `NAME=value`, with no quotes or spaces, because `--from-env-file` and `docker run --env-file` keep them literally |
| API pod | 1 replica; memory request 512 Mi, limit 1.5 Gi; startup (up to 2 min), readiness and liveness probes, all `GET /health` on port 8000 | the models are loaded before uvicorn listens, so `/health` answers only when the pod can serve |
| public URL | `http://<VM_IP>`, an Ingress with no host rule, served by k3s's Traefik | no domain to buy; HTTPS is choice 7 |
| rate limit | a Traefik `Middleware`: on average 10 requests a minute per client IP, burst 5; above that, a `429` | a public URL with no auth spends our Anthropic credit; choice 8 |
| firewall | Hetzner Cloud firewall: in 22 (SSH), 80 (HTTP), 6443 (kubectl), nothing else | Qdrant's 6333 and the API's 8000 stay closed from outside |
| kubectl from the laptop | `/etc/rancher/k3s/k3s.yaml` copied to `~/.kube/neuro-rag.yaml`, `127.0.0.1` replaced with the VM's IP; k3s installed with `--tls-san <VM_IP>` | the cluster's certificate must name the IP we connect to |
| tracing | on: the Langfuse keys are in the Secret | production requests are the ones worth tracing |

## How it is built

### Files

| File | Contents |
|---|---|
| `requirements.lock` | the API's dependencies at the laptop venv's exact versions, for Linux x86 (choice 12) |
| `Dockerfile` | the API image (below) |
| `.dockerignore` | keeps everything but `pyproject.toml` and `src/` out of the build: `.env`, `data/`, `eval/`, `docs/`, `tests/`, `.venv/`, `.git/`, the PDFs |
| `deploy/k8s/qdrant.yaml` | Qdrant: StatefulSet, Service `qdrant` (ClusterIP, port 6333) |
| `deploy/k8s/api.yaml` | API: Deployment, Service `api` (ClusterIP, port 80 → 8000) |
| `deploy/k8s/ingress.yaml` | the rate-limit Middleware and the Ingress to `api` |
| `deploy/README.md` | the steps below, as commands to copy |
| `.github/workflows/ci.yml` | choice 11 |

No Python file changes.

### `Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.lock pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.lock
COPY src ./src
RUN pip install --no-cache-dir --no-deps .
ENV FASTEMBED_CACHE_PATH=/models
RUN python -c "from fastembed import TextEmbedding, SparseTextEmbedding; \
TextEmbedding('sentence-transformers/all-MiniLM-L6-v2'); SparseTextEmbedding('Qdrant/bm25')"
EXPOSE 8000
CMD ["uvicorn", "neuro_rag.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

- `--host 0.0.0.0`: uvicorn's default `127.0.0.1` can't be reached from
  outside the container.
- The model names repeat `config.py`'s `EMBED_MODEL` and `SPARSE_MODEL`; if
  either changes, the Dockerfile changes with it (DP-1 fails otherwise).
- No `.env` inside: `load_dotenv()` finds none and the keys come from the
  Secret.

### Steps, first deploy

1. **VM:** create the CX22 with the firewall above and your SSH key.
2. **k3s:** `ssh root@<VM_IP> 'curl -sfL https://get.k3s.io | sh -s - --tls-san <VM_IP>'`,
   then copy the kubeconfig to the laptop as in Settings and
   `export KUBECONFIG=~/.kube/neuro-rag.yaml`.
3. **Image:** `docker buildx build --platform linux/amd64 -t ghcr.io/amine789/neuro-rag-api:<sha> --push .`
   (after `docker login ghcr.io` with a GitHub token that has `write:packages`;
   then set the package to public on GitHub once).
4. **Secret:** `kubectl create secret generic neuro-rag-keys --from-env-file=.env`.
5. **Qdrant:** `kubectl apply -f deploy/k8s/qdrant.yaml`, wait for `qdrant-0` Ready.
6. **Index:** on the laptop, `curl -X POST localhost:6333/collections/papers/snapshots`
   and download the snapshot it names; then
   `kubectl port-forward svc/qdrant 6334:6333` and
   `curl -X POST 'localhost:6334/collections/papers/snapshots/upload?priority=snapshot' -F snapshot=@papers.snapshot`.
   (6334 on the laptop, so it doesn't clash with the local Qdrant on 6333.)
7. **API and URL:** set the image tag in `api.yaml`, then
   `kubectl apply -f deploy/k8s/`.

**Later deploys:** steps 3 and 7 only, with the new commit's hash.

## Choices, accepted 2026-11-16

1. **k3s on one Hetzner CX22.** Alternatives: a managed cluster (EKS, GKE,
   DOKS: $70+ a month with a load balancer); a 4 GB droplet on DigitalOcean
   (~$24); plain `docker compose` on the VM (simpler, but not Kubernetes,
   which the roadmap asks for).
2. **The image on ghcr.io, public, tagged by commit.** Building on the VM and
   importing into k3s avoids a registry, but CD needs one anyway.
3. **Models downloaded at build time.** The image is ~150 MB larger; the pod
   starts with no network fetch and the same model files every time.
4. **The index moved as a Qdrant snapshot,** not rebuilt on the server.
   Rebuilding needs the 206 MB of PDFs, GROBID and 4 minutes there, and could
   give different chunks if anything drifted; a snapshot is the same index.
5. **Plain YAML and `kubectl apply`.** Helm or Kustomize would be machinery
   for three files.
6. **Keys in a Secret made from `.env`.** Secrets in k3s are stored base64,
   not encrypted, on the VM's disk; accepted for this project (anyone with root
   on the VM could read them, as they could read `.env` on the laptop).
7. **HTTP only, on the bare IP.** Questions travel in clear text. HTTPS needs
   a hostname (free with `<VM_IP>.sslip.io`) plus cert-manager and a Let's
   Encrypt issuer: one install and one more YAML. Candidate for later in this
   row or after it.
8. **A rate limit now, not after row 12.** The roadmap put rate limits after
   row 12, but a public URL with no auth lets anyone spend the Anthropic
   credit; this is configuration (one Middleware), not code. 10 a minute per
   IP; the prepaid credit is the hard cap behind it.
9. **One replica each, no autoscaling.** One VM is one point of failure,
   accepted.
10. **The eval runs against the deployment through a port-forward.**
    `run.py` needs the hits (for page@5 and faithfulness), which the API
    doesn't return, so the eval runs on the laptop with `QDRANT_URL` pointed at
    the deployed Qdrant: it measures the deployed index with the same code and
    model. A free check first (DP-8: every question's top 5 chunks equal the
    laptop's); the full eval (DP-10, ~$0.26) after a top-up.
11. **CI now, CD later.** A GitHub Actions workflow runs the free tests
    (`pytest -m "not integration and not llm"`) on every push and pull
    request. CD (build, push, `kubectl set image`) is added once the manual
    deploy above has worked; it would need the kubeconfig as a GitHub secret.
12. **Dependencies pinned in `requirements.lock`** (added 2026-11-16, after
    the first build). `pyproject.toml` has no versions, so the first image
    took the newest of everything: anthropic 2.9.0 and langfuse 5.2.0 against
    the laptop's 1.8.0 and 4.17.0, both new major versions. The lock is made
    from the laptop's venv with `uv pip compile` for Linux x86 (86 packages,
    each at the venv's version), and the Dockerfile installs it before the
    code, so a code change rebuilds only the last layers. Upgrading a package
    becomes a deliberate change: upgrade the venv, rerun the tests, remake
    the lock.
    DP-3 then found `langchain` missing: `langfuse.langchain` imports it, the
    venv had it from earlier work, but `pyproject.toml` never listed it. It is
    now a dependency (pinned at the venv's 1.4.2).

## Acceptance criteria

Each criterion is one concrete example, written so it can be read on its own.
How each one is checked is in [validation.md](validation.md).

### The image (laptop, free)

**DP-1: the image holds the models and starts without downloading.**
- **Given** the image built from the Dockerfile.
- **When** `docker run --rm --network none <image> python -c "from fastembed import TextEmbedding, SparseTextEmbedding; TextEmbedding('sentence-transformers/all-MiniLM-L6-v2'); SparseTextEmbedding('Qdrant/bm25')"` runs.
- **Then** it exits 0 with no network.
- **Why:** a pod that downloads models at start is slow and breaks when the
  model host is down.

**DP-2: no key is in the image.**
- **Given** the image.
- **When** `docker run --rm <image> ls -a /app` and
  `docker history --no-trunc <image>` and `docker image inspect <image>` run.
- **Then** there is no `.env` in `/app`, and neither "sk-ant" nor "sk-lf"
  appears in the history or the inspect output.
- **Why:** the image is public on ghcr.io.

**DP-3: the image serves the API on the laptop.**
- **Given** the local Qdrant running.
- **When** `docker run --rm --env-file .env -e QDRANT_URL=http://host.docker.internal:6333 -p 8000:8000 <image>`
  runs and q01 is sent with row 5's curl.
- **Then** `/health` gives `{"status":"ok"}` and q01 gets a 200 whose sources
  include PMC6226095.
- **Why:** the image is checked before it leaves the laptop. (~$0.003)

### The cluster

**DP-4: both pods run and are ready.**
- **Given** the steps above done.
- **When** `kubectl get pods` runs.
- **Then** `qdrant-0` and one `api-…` pod show `1/1 Running`.

**DP-5: the deployed index is the laptop's.**
- **Given** the snapshot restored.
- **When** `curl localhost:6334/collections/papers` runs through the port-forward.
- **Then** `points_count` is 4313.

**DP-6: the public URL answers.**
- **Given** the Ingress applied.
- **When** from the laptop, `curl http://<VM_IP>/health` and row 5's q01 curl
  against `http://<VM_IP>/ask` run.
- **Then** `{"status":"ok"}`, and a 200 whose sources include PMC6226095.
  (~$0.003)
- **Why:** the row's "done when".

**DP-7: only the API is public.**
- **When** `curl -m 5 http://<VM_IP>:6333/collections` and
  `curl -m 5 http://<VM_IP>:8000/health` run from the laptop.
- **Then** both fail (timeout or connection refused).
- **Why:** an open Qdrant could be read or wiped by anyone.

**DP-8: search on the deployed index gives the laptop's top 5 for every question.**
- **Given** `kubectl port-forward svc/qdrant 6334:6333`.
- **When** `QDRANT_URL=http://localhost:6334 python scripts/compare_search.py` runs.
- **Then** its CSV's `chunk_ids` equal `eval/results/search_compare_2026-11-04.csv`'s
  on every row (`diff` shows nothing but the file name), and it prints dense
  paper@5 and page@5 equal to that run's.
- **Why:** free proof that the deployed index answers search exactly like the
  laptop's, so the baseline's retrieval numbers hold on the deployment.

**DP-9: data survives a restart.**
- **When** `kubectl delete pod qdrant-0` and `kubectl delete pod -l app=api` run,
  and the pods come back Ready.
- **Then** `points_count` is still 4313, and q01 on the public URL still
  gets a 200. (~$0.003)
- **Why:** a pod restart (a crash, a node reboot, a new image) must not lose
  the index.

**DP-10: the full eval runs against the deployment.** *(after a top-up; ~$0.26)*
- **Given** the port-forward of DP-8.
- **When** `QDRANT_URL=http://localhost:6334 python -m neuro_rag.eval.run --name deployed` runs.
- **Then** 50 runs, 0 failed; paper@5, page@5, cites expected and not covered
  equal the baseline's (search is deterministic); correctness and faithful
  within 0.05 of the baseline's (the LLM varies).
- **Why:** the roadmap's "the eval runs against it".

### Around the cluster

**DP-11: the rate limit protects the credit.**
- **When** `for i in $(seq 20); do curl -s -o /dev/null -w '%{http_code} ' http://<VM_IP>/health; done` runs.
- **Then** some of the 20 codes are `429`.
- **Why:** choice 8; `/health` is used so the check costs nothing.

**DP-12: a production request is traced.**
- **Given** DP-6's request.
- **Then** Langfuse has its trace as in TR-2 (`ask` → `search`, `answer` →
  `ChatAnthropic`, with tokens and cost).

**DP-13: CI runs the free tests on every push.**
- **Given** `.github/workflows/ci.yml` pushed.
- **When** a commit is pushed to `v3`.
- **Then** the GitHub Actions run is green, and its log shows the free tests
  passed and the `integration`/`llm`/`langfuse` tests deselected.
- **Why:** choice 11; a red run on a broken push is what CI is for.

## Out of scope

- CD (choice 11), HTTPS (choice 7), a domain name.
- More than one node, replicas, autoscaling, backups of the volume.
- Auth and client keys (after row 12).
- Running the eval inside the cluster.
- A readiness check that pings Qdrant (row 5 choice 8 left it here; the
  `/health` probe stays as it is, since the API returns a 503 anyway when
  Qdrant is down).
