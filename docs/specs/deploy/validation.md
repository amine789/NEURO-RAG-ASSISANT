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
| DP-8 | eval | `compare_search.py` on the deployed index; dense rows' `chunk_ids` and all rows' hits against 2026-11-04's |
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
| 2026-11-18 | v3, `c1f42cd` (image `148b1db`) | DP-5 passed | Qdrant on the VM restored from the laptop's snapshot: 4313 points |

### 2026-11-18 details (the cluster, part 1)

- **VM:** Hetzner CPX22, Helsinki, `204.168.182.10`; k3s v1.37.2+k3s1; `kubectl get nodes` shows one node `Ready`.
- **Image:** `ghcr.io/amine789/neuro-rag-api:148b1db` pushed and public (an anonymous pull request got 200).
- **Secret:** `neuro-rag-keys` created from `.env` (7 entries).
- **Qdrant:** `qdrant-0` `1/1 Running`; snapshot `papers-8328499992741243-2026-11-18-16-24-54.snapshot`
  (28,075,008 bytes, sha256 `f73a77fe…a7f080`, matching Qdrant's checksum) uploaded through
  `kubectl port-forward svc/qdrant 6334:6333`.
- **DP-5:** `points_count` 4313.
- **Snags, for the record:** a new terminal without `KUBECONFIG` made kubectl try `localhost:8080`;
  a stopped port-forward made the first count fail with an empty answer (and `curl -s` hid the failed upload).
  Each step and its fix is in `docs/deploy-commands-explained.pdf`.
| 2026-11-18 | v3 (image `148b1db`) | live; DP-6 and DP-7 passed | `http://204.168.182.10/ask` answers from the internet |

### 2026-11-18 details (the cluster, part 2: live)

- **Step 5:** the image tag set in `api.yaml` (`148b1db`), then `kubectl apply -f deploy/k8s/`
  created the API Deployment and Service, the rate-limit Middleware and the Ingress (Qdrant unchanged).
- **DP-6:** `curl http://204.168.182.10/health` gave `{"status":"ok"}`; q01 on
  `http://204.168.182.10/ask` gave a 200 with three sentences cited `[1]`, PMC6226095 page 6.
- **DP-7:** from outside, `204.168.182.10:6333` and `:8000` don't answer (curl code 000); only port 80 is public.
- **DP-4:** `kubectl get pods`: `qdrant-0` and the `api-…` pod both `1/1 Running`.
- **DP-12:** the public q01 request left its trace in Langfuse (`ask` → `search`, `answer` → `ChatAnthropic`).
- **DP-11:** 20 fast `/health` calls from one IP: the first 5 got `200` (the burst), the rest `429`.
- **DP-9:** `kubectl delete pod qdrant-0` and `kubectl delete pod -l app=api`; both came back
  `1/1 Running`, `points_count` still 4313, q01 on the public URL still answered.
- **DP-8 (passed, after rewording):** `compare_search.py` through the port-forward
  (`eval/results/search_compare_2026-11-18.csv`) against 2026-11-04's:
  - dense, the mode the API and the eval use: 40 of 40 rows identical (same 5 chunks, same order);
    page@5 24 vs 24;
  - hybrid: same paper@5 and page@5 hits on all 40 rows (page@5 23 vs 23); 12 rows differ in the
    chunks themselves (neighbours swap places in 8, one chunk swapped in 4, e.g. q06's 3rd and 4th),
    likely near-ties in the rank fusion and Qdrant's approximate search after the restore, not proven.
  - The criterion first said every row's `chunk_ids`; reworded the same day (with approval) to
    "dense identical, hybrid hits unchanged", since hybrid is not used in production.
- **DP-13 prep:** `.github/workflows/ci.yml` written (free tests, pinned versions). IN-11 marked
  `integration`: it reads `data/tei/PMC6226095.tei.xml`, which is gitignored, so it would fail on
  GitHub's machine; it stays a laptop test.
- **Still to check:** DP-10 (after a top-up), DP-13 (push and see the run).
