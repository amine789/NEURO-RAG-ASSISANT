# Corrective RAG loop: validation

How each acceptance criterion in [spec.md](spec.md) is checked, and the results.

## Checks

- **Scripts** (phase 1): G3's data and training (about $0.50 once, for the
  synthetic questions), then the grader comparison (free: all four graders run locally).
- **Unit** (`tests/test_crag.py`, free): the loop with fakes; no Qdrant, no API call.
- **By hand:** the server with tracing on, and the Langfuse UI.
- **Eval** (about $0.30): `python -m neuro_rag.eval.run --name crag --rerank --crag`.

| Criterion | Kind | Check |
|---|---|---|
| CR-1 | script | `fetch_grader_papers.py` then `make_grader_data.py`: 40 new papers, none in the corpus; sizes, drops, no paper in both splits |
| CR-2 | script | `python scripts/train_grader.py`: dev accuracy above the un-tuned reranker's |
| CR-3 | script | `python scripts/compare_graders.py`: the four-grader table and the choice |
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
