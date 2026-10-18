# Eval report: baseline + rerank

- system model: claude-haiku-5-5; judge model: claude-haiku-5-5; index: hippocampus-v1
- 162 runs (3 repeats, 4 at a time); 0 failed; 0 not judged

Correctness: correct 1, partial 0.5, wrong 0. Rates are fractions of the runs each measure applies to; – means it applies to none. Latency is retrieval plus generation.
| questions | runs | correctness | faithful | retrieval hit | cites expected | not covered | p50 s | p95 s | $ per answer |
|---|---|---|---|---|---|---|---|---|---|
| all (excl. multilingual) | 150 | 0.69 | 0.84 | 0.92 | 0.84 | 1.00 | 2.8 | 4.7 | 0.0005 |
| borderline | 18 | – | – | – | – | – | 1.7 | 2.1 | 0.0003 |
| broad_vague | 3 | 0.00 | – | 1.00 | 0.00 | – | 2.6 | 2.7 | 0.0005 |
| casual | 9 | 0.56 | 0.56 | 1.00 | 1.00 | – | 3.6 | 6.2 | 0.0006 |
| casual_loose_terms | 12 | 0.25 | 0.71 | 0.25 | 0.25 | – | 3.3 | 4.6 | 0.0006 |
| casual_multi_paper | 3 | 0.50 | 1.00 | 1.00 | 1.00 | – | 4.6 | 5.5 | 0.0007 |
| casual_typos | 3 | 0.83 | 0.67 | 1.00 | 1.00 | – | 4.5 | 4.7 | 0.0007 |
| clinical_loose | 3 | 0.50 | 0.67 | 1.00 | 1.00 | – | 4.4 | 4.8 | 0.0007 |
| direct | 21 | 0.86 | 0.90 | 1.00 | 1.00 | – | 2.5 | 3.8 | 0.0005 |
| direct_computational | 3 | 1.00 | 1.00 | 1.00 | 1.00 | – | 3.4 | 3.8 | 0.0006 |
| direct_human | 6 | 1.00 | 1.00 | 1.00 | 1.00 | – | 3.6 | 4.1 | 0.0006 |
| false_premise | 6 | 1.00 | 1.00 | 1.00 | 1.00 | – | 2.7 | 3.4 | 0.0006 |
| false_premise_casual | 3 | 0.50 | 1.00 | 1.00 | 1.00 | – | 3.2 | 3.4 | 0.0006 |
| false_premise_keywords | 3 | 1.00 | 1.00 | 1.00 | 1.00 | – | 2.9 | 2.9 | 0.0005 |
| keywords | 3 | 1.00 | 1.00 | 1.00 | 1.00 | – | 3.9 | 4.0 | 0.0007 |
| keywords_typos | 6 | 0.83 | 1.00 | 1.00 | 1.00 | – | 3.8 | 4.5 | 0.0007 |
| loose_terms | 6 | 0.58 | 0.50 | 1.00 | 0.67 | – | 3.7 | 4.6 | 0.0006 |
| multi_paper | 6 | 0.75 | 0.83 | 1.00 | 1.00 | – | 3.9 | 5.3 | 0.0008 |
| multilingual_ar | 3 | 0.00 | – | 0.00 | 0.00 | – | 1.8 | 1.9 | 0.0002 |
| multilingual_de | 3 | 0.00 | – | 0.00 | 0.00 | – | 2.0 | 2.3 | 0.0004 |
| multilingual_es | 3 | 0.00 | – | 0.00 | 0.00 | – | 1.8 | 1.9 | 0.0004 |
| multilingual_fr | 3 | 0.00 | – | 0.00 | 0.00 | – | 1.8 | 1.9 | 0.0004 |
| negative_result | 3 | 1.00 | 1.00 | 1.00 | 1.00 | – | 3.3 | 3.6 | 0.0006 |
| non_native_grammar | 3 | 1.00 | 1.00 | 1.00 | 1.00 | – | 3.2 | 3.4 | 0.0006 |
| off_domain | 15 | – | – | – | – | 1.00 | 1.6 | 2.3 | 0.0003 |
| off_domain_casual | 3 | – | – | – | – | 1.00 | 1.1 | 1.4 | 0.0003 |
| out_of_corpus | 3 | – | – | – | – | 1.00 | 1.6 | 2.8 | 0.0003 |
| out_of_corpus_casual | 3 | – | – | – | – | 1.00 | 2.2 | 2.3 | 0.0003 |
| rambling_personal | 3 | 0.67 | 0.33 | 1.00 | 1.00 | – | 4.6 | 4.7 | 0.0007 |
| typos | 3 | 0.00 | – | 1.00 | 0.00 | – | 2.8 | 3.4 | 0.0005 |
