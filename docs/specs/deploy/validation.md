# Deployment: validation

How each acceptance criterion in [spec.md](spec.md) is checked, and the results.
The examples are in the spec; this file says where each one runs.

## Checks

- **Laptop:** docker commands on the built image. Free, except DP-3 (~$0.003).
- **Cluster:** `kubectl` and curl from the laptop, with
  `KUBECONFIG=~/.kube/neuro-rag.yaml`. Each q01 request ~$0.003.
- **Eval:** the laptop's eval and search script against the deployed Qdrant
  through `kubectl port-forward svc/qdrant 6334:6333`.
- **GitHub:** the Actions tab.

| Criterion | Kind | Check |
|---|---|---|
| DP-1 | laptop | the image loads both models with `--network none` |
| DP-2 | laptop | no `.env` in `/app`; no "sk-ant"/"sk-lf" in `docker history` or `docker image inspect` |
| DP-3 | laptop | `docker run` with `.env`; `/health` and q01 |
| DP-4 | cluster | `kubectl get pods`: both `1/1 Running` |
| DP-5 | cluster | `points_count` 4313 through the port-forward |
| DP-6 | cluster | `/health` and q01 on `http://<VM_IP>` |
| DP-7 | cluster | ports 6333 and 8000 closed from outside |
| DP-8 | eval | `compare_search.py` on the deployed index; `diff` the CSV against 2026-11-04's |
| DP-9 | cluster | delete both pods; count and q01 again |
| DP-10 | eval | `eval.run --name deployed` (after a top-up) |
| DP-11 | cluster | 20 fast `/health` calls; some `429` |
| DP-12 | Langfuse | DP-6's trace |
| DP-13 | GitHub | a push to `v3`; the run is green |

## Results

| Date | Version | Result | Notes |
|---|---|---|---|
| 2026-11-16 | v3, uncommitted | spec written, choices 1–12 accepted | not built yet |
| 2026-11-17 | v3, uncommitted | DP-1, DP-2, DP-3 passed on the laptop | image `neuro-rag-api:local`, built from `requirements.lock` |

### 2026-11-17 details (the image, on the laptop)

- **Versions:** inside the image, anthropic 1.8.0, langfuse 4.17.0, langchain-core 1.6.5,
  fastapi 0.141.1, qdrant-client 1.19.1, the laptop's (choice 12).
- **DP-1:** both models load with `--network none`.
- **DP-2:** no `.env` in `/app`; no "sk-ant" or "sk-lf" in `docker history` or `docker image inspect`.
- **DP-3:** `/health` ok; q01 got a 200 with three sentences cited `[1]`, PMC6226095 page 6.
- **Found on the way, all fixed:**
  - the first build took the newest packages (anthropic 2.9.0, langfuse 5.2.0): pinned with
    `requirements.lock` (choice 12);
  - `langchain` was missing: `langfuse.langchain` imports it; added to `pyproject.toml`;
  - `.env` values had quotes and a space after `=`: `load_dotenv()` strips them, but
    `docker run --env-file` (and `kubectl create secret --from-env-file`) keep them literally,
    so the keys and the Langfuse URL were broken inside the container ("Connection error",
    host `"https`). `.env` is now `NAME=value` with nothing around the value.
