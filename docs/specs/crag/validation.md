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
| 2026-11-21 | v3, uncommitted | CR-3 run 1 (`eval/results/2026-11-21_0013_graders/`): Gemma 3 1B on 44 labelled questions (32 good, 12 weak; 6 borderline left out); hits identical to row 8's on all 44 | accuracy 0.795 (35/44); weak judged good 5 (q12, q33, q36: row 8 answered wrong; q43 web_fallback ketamine; q54 decline "Which programming language should I learn first?" at 0.99); good judged weak 4 (q14, q23, q29 casual wording, q42 false premise); 0 errors; latency median 7.13 s, p95 9.5 s, max 12.5 s a grade on the laptop CPU: misses the p95 ≤ 6 s target before the answer is even written. Always saying "good" would score 32/44 = 0.727, so the gain is +0.07 |
| 2026-11-21 | v3, uncommitted | CR-3 run 2 (`eval/results/2026-11-21_0021_graders/`): Haiku 4.5 as grader, same prompt, same 44 questions and hits | accuracy 0.841 (37/44); weak judged good 1 (q12, which row 8 answered wrong); good judged weak 6, 4 of them false-premise questions (q17, q18, q41, q42: Haiku says the passages can't answer a question whose premise they contradict) plus q27 and q30; 0 errors; latency median 0.48 s, p95 0.54 s, one outlier at 75.9 s (likely an API retry); about $0.0011 a grade, about $0.05 for the run. Against Gemma 3 1B: +0.05 accuracy, 1 costly mistake instead of 5 (q54 and q43 now weak), 15× faster. Paid, against choice 12 (free graders): to decide |
| 2026-11-21 | v3, uncommitted | Laya first try: every request a 500 | llama.cpp log: "input (852 tokens) is too large to process. increase the physical batch size (current batch size: 512)"; an encoder takes its whole input in one batch; fixed with `-c 4096 -b 4096 -ub 4096` in docker-compose.yml |
| 2026-11-21 | v3, uncommitted | CR-3 run 3 (`eval/results/2026-11-21_0032_graders/`): Laya (Q8_0), same 44 questions and hits | accuracy 0.818 (36/44); weak judged good 6 (q06, q12, q33, q36 row 8 wrong; q43 web_fallback; q54 "programming language" at 0.82); good judged weak 2 (q13, q42); 0 errors; latency median 4.93 s, p95 7.5 s, max 10.2 s on the laptop CPU; scores only span 0.10 to 0.85 and 6 of the 8 mistakes sit between 0.35 and 0.61, so its yes/no is barely separated around the 0.5 cut |
