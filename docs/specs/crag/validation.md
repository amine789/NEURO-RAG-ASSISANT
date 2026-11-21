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
| 2026-11-21 | v3, uncommitted | jury labels decided (choice 18) | GPT-5.6 Sol, Gemini Pro (latest), Grok 4.7 via OpenRouter, majority of 3, retrieval sufficiency; runs 1-3 above used the row 8 proxy and are re-run on the jury labels |
| 2026-11-21 | v3, uncommitted | jury labels (`eval/ground_truth/`): 150 votes, 0 failed, $0.84; `~google/gemini-pro-latest` resolved to `google/gemini-4-carbon` | 50 labelled: 30 good, 20 weak; **47/50 unanimous**; agreement with the majority: GPT-5.6 Sol 50/50, Gemini 49/50, Grok 48/50. Against the row 8 proxy, 11 differ: q12 weak → good (the proxy's "wrong" answer came from good chunks); q16, q25, q30, q31 good → weak (row 8 answered correctly without sufficient chunks, so from Claude's own knowledge); the 6 borderline questions now labelled (q46 good 2-1, q45 and q47–q50 weak). q33 and q36 stay weak |
| 2026-11-21 | v3, uncommitted | Jev re-added via OpenRouter (choice 19) | `typesafe/jev-1.14` at /api/v1/systemone, about $0.00004 a grade; OpenJev local ruled out (19 GB Q4) |
| 2026-11-21 | v3, uncommitted | **CR-3 run 4, jury labels** (`eval/results/2026-11-21_1647_graders_jury/`): four graders, 50 questions (30 good, 20 weak), hits identical to row 8's on all 50 | accuracy / weak→good / good→weak / median s: Gemma 1B 0.74 / 8 / 5 / 1.39; Laya 0.76 / 10 / 2 / 4.49; **Jev 0.84 / 5 / 3 / 0.35** (~$0.00004); **Haiku 0.84 / 3 / 5 / 0.74** (~$0.0011); 0 errors. Rule: Jev and Haiku tie on accuracy, Haiku has fewer weak judged good, **chosen: Haiku**. Always "good" would score 30/50 = 0.60. All four call q16, q25, q31 good where the jury says weak (on-topic chunks missing the key facts); Haiku and Jev both miss false-premise q17 and q42 (Haiku also q18 and q41); Jev's q36 scored exactly 0.5 (good at the cut). Gemma's 1.39 s median is much lower than run 1's 7.1 s on the same prompts, most likely llama.cpp's prompt cache from the earlier runs, so not its real latency; p95 6.4 s. Laya p95 6.4 s, Jev 0.43 s, Haiku 0.87 s |
| 2026-11-21 | v3, uncommitted | Jev alone, same day (`eval/results/2026-11-21_1640_graders_jury/`) | accuracy 0.88, weak→good 4, good→weak 2, against 0.84 / 5 / 3 in run 4. Jev is not deterministic: 22 of 50 scores differ between the two runs, by 0.01 to 0.04; two decisions flip because they sit at the cut (q18 0.50 → 0.46, q36 0.47 → 0.50; Jev reports two decimals, so 0.50 lands exactly on it). The 0.84 vs 0.88 gap is noise of one or two questions; a single run can't separate Jev from Haiku |
| 2026-11-21 | v3, uncommitted | CR-3 run 5, Jev and Haiku × 3 (`eval/results/2026-11-21_1701_graders_jury/`), jury labels | mean ± std over 3 runs: **Jev accuracy 0.860 ± 0.000, weak→good 4.0 ± 0, good→weak 3.0 ± 0, median 0.33 s**; **Haiku 0.840 ± 0.000, weak→good 3.0 ± 0, good→weak 5.0 ± 0, median 0.68 s**. No variation inside this run, although Jev's two earlier runs the same day gave 0.84 and 0.88: over all 5 Jev runs, accuracy 0.86 ± 0.014 (0.84 to 0.88), weak→good 4.2 (4 to 5). Haiku is stable at 0.84 / 3 / 5 over 4 runs. By the rule (within 0.05, then fewer weak judged good) Haiku is chosen, by one question; Jev is 25× cheaper and 2× faster |
| 2026-11-21 | v3, uncommitted | **grader chosen: Jev** (choice 20, override) | the rule picks Haiku by one weak-judged-good question (3 vs 4), within Jev's range; Jev better on accuracy (0.86 vs 0.84), good judged weak (3 vs 5), latency (0.33 vs 0.68 s) and cost (25×) |
