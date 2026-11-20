# Corrective RAG loop: validation

How each acceptance criterion in [spec.md](spec.md) is checked, and the results.

## Checks

- **Scripts** (phase 1): the grader comparison (free: G2b and G3 run locally). G1's
  data and training (about $0.50 once, for the synthetic questions) only if
  G1 is built (choice 15).
- **Unit** (`tests/test_crag.py`, free): the loop with fakes; no Qdrant, no API call.
- **By hand:** the server with tracing on, and the Langfuse UI.
- **Eval** (about $0.30): `python -m neuro_rag.eval.run --name crag --rerank --crag`.

| Criterion | Kind | Check |
|---|---|---|
| CR-1 | script, deferred (choice 15) | `fetch_grader_papers.py` then `make_grader_data.py`: 40 new papers, none in the corpus; sizes, drops, no paper in both splits |
| CR-2 | script, deferred (choice 15) | `python scripts/train_grader.py`: dev accuracy above the un-tuned reranker's |
| CR-3 | script | `python scripts/compare_graders.py`: the grader table (G2b, G3, plus G1 if built) and the choice |
| CR-4 | unit | `test_CR4_good_retrieval_answers_directly` |
| CR-5 | unit | `test_CR5_weak_rewritten_original_answered` |
| CR-6 | unit | `test_CR6_stops_after_max_rewrites_then_web` |
| CR-7 | unit | `test_CR7_weak_everywhere_not_covered_no_answer_call` |
| CR-8 | unit | `test_CR8_failures_degrade_never_crash` |
| CR-9 | unit | `test_CR9_web_hits_allow_list_and_page_url` |
| CR-10 | unit | `test_api.py`: AP-1 updated, plus `test_CR10_api_returns_path` |
| CR-11 | by hand | a rewrite-path question's trace in Langfuse |
| CR-12 | eval | the crag report against `2026-11-18_2157_rerank` |

## Results

| Date | Version | Result | Notes |
|---|---|---|---|
| 2026-11-18 | v3, uncommitted | spec written | one grader (threshold), one rewrite |
| 2026-11-19 | v3, uncommitted | spec rewritten | four graders compared (threshold, Jev, fine-tuned, Haiku); bounded loop, 2 rewrites; choices 1–10 to confirm |
| 2026-11-19 | v3, uncommitted | threshold grader removed | three graders: Jev, fine-tuned, Haiku |
| 2026-11-19 | v3, uncommitted | Laya added as G4 | four graders: Jev, fine-tuned, Haiku, Laya |
| 2026-11-19 | v3, uncommitted | choices 1–11 accepted | not built yet |
| 2026-11-19 | v3, uncommitted | Gemma 3 1B replaces Haiku as G3 (choice 12) | the four graders: Jev, fine-tuned, Gemma, Laya |
| 2026-11-19 | v3, uncommitted | choice 4 updated: Jev's provider chosen by a documented HTTP endpoint | routes: TypeSafe, AIMLAPI, Vercel AI Gateway, OpenRouter |
| 2026-11-20 | v3, uncommitted | Jev dropped (paid) | three free graders: fine-tuned (G1), Gemma (G2), Laya (G3) |
| 2026-11-20 | v3, uncommitted | Liquid d1 added as G4 (choice 13) | four free graders: fine-tuned, Gemma, Laya, Liquid d1 |
| 2026-11-20 | v3, uncommitted | G1 trains on 40 new papers (choice 14) | no indexed or eval paper in its training data |
| 2026-11-20 | v3, uncommitted | G1 deferred (choice 15) | G2–G4 compared first; G1, CR-1 and CR-2 only if CR-12 fails |
| 2026-11-20 | v3, uncommitted | Liquid d1 removed, Gemma 3 270M added (choice 16) | graders: Gemma 270M (G2a), Gemma 1B (G2b), Laya (G3); G1 deferred |
| 2026-11-20 | v3, uncommitted | Gemma 3 270M smoke test: P(yes) 0.96 hippocampus question, 0.92 sourdough question | says yes regardless; dropped (choice 17); Gemma 3 1B next |
| 2026-11-20 | v3, uncommitted | Gemma 3 1B smoke test: P(yes) 0.9998 hippocampus question, 0.0000002 sourdough question | separates relevant from off-topic; next: compare_graders.py on the eval |
