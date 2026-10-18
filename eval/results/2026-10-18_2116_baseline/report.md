# Eval report: baseline (retrieve -> generate)

- system model: claude-haiku-5-5; judge model: claude-haiku-5-5; index: hippocampus-v1
- 162 runs (3 repeats, 4 at a time); 0 failed; 0 not judged

Correctness: correct 1, partial 0.5, wrong 0. Rates are fractions of the runs each measure applies to; – means it applies to none. Latency is retrieval plus generation.
| questions | runs | correctness | faithful | retrieval hit | cites expected | not covered | p50 s | p95 s | $ per answer |
|---|---|---|---|---|---|---|---|---|---|
| all (excl. multilingual) | 150 | 0.68 | 0.80 | 0.88 | 0.84 | 1.00 | 2.5 | 4.8 | 0.0005 |
| borderline | 18 | – | – | – | – | – | 1.2 | 2.6 | 0.0003 |
| broad_vague | 3 | 0.00 | – | 0.00 | 0.00 | – | 1.8 | 2.0 | 0.0004 |
| casual | 9 | 0.44 | 0.75 | 1.00 | 0.89 | – | 3.3 | 4.6 | 0.0006 |
| casual_loose_terms | 12 | 0.12 | 0.80 | 0.25 | 0.00 | – | 2.4 | 3.5 | 0.0005 |
| casual_multi_paper | 3 | 0.50 | 0.67 | 1.00 | 1.00 | – | 3.9 | 4.4 | 0.0007 |
| casual_typos | 3 | 0.67 | 0.67 | 1.00 | 1.00 | – | 4.3 | 4.5 | 0.0007 |
| clinical_loose | 3 | 0.50 | 1.00 | 1.00 | 1.00 | – | 4.8 | 5.6 | 0.0008 |
| direct | 21 | 0.79 | 0.86 | 1.00 | 1.00 | – | 2.1 | 6.6 | 0.0005 |
| direct_computational | 3 | 1.00 | 0.67 | 1.00 | 1.00 | – | 2.3 | 2.3 | 0.0005 |
| direct_human | 6 | 1.00 | 0.67 | 1.00 | 1.00 | – | 2.6 | 3.9 | 0.0006 |
| false_premise | 6 | 0.92 | 0.83 | 1.00 | 1.00 | – | 3.0 | 3.5 | 0.0006 |
| false_premise_casual | 3 | 0.50 | 0.33 | 1.00 | 1.00 | – | 2.6 | 2.9 | 0.0005 |
| false_premise_keywords | 3 | 1.00 | 1.00 | 1.00 | 1.00 | – | 2.5 | 3.1 | 0.0005 |
| keywords | 3 | 1.00 | 0.67 | 1.00 | 1.00 | – | 3.3 | 3.4 | 0.0006 |
| keywords_typos | 6 | 0.92 | 0.83 | 1.00 | 1.00 | – | 3.6 | 4.2 | 0.0007 |
| loose_terms | 6 | 1.00 | 1.00 | 1.00 | 1.00 | – | 3.0 | 4.4 | 0.0006 |
| multi_paper | 6 | 0.58 | 0.83 | 1.00 | 1.00 | – | 3.9 | 6.1 | 0.0008 |
| multilingual_ar | 3 | 0.00 | – | 0.00 | 0.00 | – | 1.4 | 1.6 | 0.0003 |
| multilingual_de | 3 | 0.00 | – | 0.00 | 0.00 | – | 1.7 | 2.4 | 0.0004 |
| multilingual_es | 3 | 0.00 | – | 0.00 | 0.00 | – | 1.5 | 1.6 | 0.0003 |
| multilingual_fr | 3 | 0.00 | – | 0.00 | 0.00 | – | 1.5 | 1.5 | 0.0003 |
| negative_result | 3 | 1.00 | 0.67 | 1.00 | 1.00 | – | 3.1 | 3.3 | 0.0006 |
| non_native_grammar | 3 | 1.00 | 1.00 | 1.00 | 1.00 | – | 2.2 | 2.4 | 0.0005 |
| off_domain | 15 | – | – | – | – | 1.00 | 1.3 | 1.5 | 0.0003 |
| off_domain_casual | 3 | – | – | – | – | 1.00 | 0.8 | 1.2 | 0.0003 |
| out_of_corpus | 3 | – | – | – | – | 1.00 | 0.8 | 1.0 | 0.0002 |
| out_of_corpus_casual | 3 | – | – | – | – | 1.00 | 1.0 | 1.3 | 0.0003 |
| rambling_personal | 3 | 1.00 | 1.00 | 1.00 | 1.00 | – | 4.7 | 4.7 | 0.0007 |
| typos | 3 | 0.00 | 0.67 | 0.67 | 0.67 | – | 4.6 | 4.8 | 0.0007 |
