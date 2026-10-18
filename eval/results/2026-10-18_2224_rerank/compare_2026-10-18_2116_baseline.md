# Comparison: 2026-10-18_2224_rerank vs 2026-10-18_2116_baseline

| questions | score | 2026-10-18_2116_baseline | 2026-10-18_2224_rerank | difference |
|---|---|---|---|---|
| all (excl. multilingual) | $ per answer | 0.0005 | 0.0005 | +0.0000 |
| all (excl. multilingual) | cites expected | 0.84 | 0.85 | +0.01 |
| all (excl. multilingual) | correctness | 0.68 | 0.75 | +0.07 |
| all (excl. multilingual) | faithful | 0.80 | 0.81 | +0.01 |
| all (excl. multilingual) | not covered | 1.00 | 1.00 | +0.00 |
| all (excl. multilingual) | p95 s | 4.8 | 6.4 | +1.56 |
| all (excl. multilingual) | retrieval hit | 0.88 | 0.89 | +0.01 |
| borderline | $ per answer | 0.0003 | 0.0003 | +0.0000 |
| borderline | p95 s | 2.6 | 3.7 | +1.05 |
| broad_vague | $ per answer | 0.0004 | 0.0004 | -0.0000 |
| broad_vague | cites expected | 0.00 | 0.00 | +0.00 |
| broad_vague | correctness | 0.00 | 0.00 | +0.00 |
| broad_vague | p95 s | 2.0 | 2.5 | +0.46 |
| broad_vague | retrieval hit | 0.00 | 0.00 | +0.00 |
| casual | $ per answer | 0.0006 | 0.0006 | +0.0000 |
| casual | cites expected | 0.89 | 1.00 | +0.11 |
| casual | correctness | 0.44 | 0.78 | +0.33 |
| casual | faithful | 0.75 | 0.67 | -0.08 |
| casual | p95 s | 4.6 | 6.4 | +1.84 |
| casual | retrieval hit | 1.00 | 1.00 | +0.00 |
| casual_loose_terms | $ per answer | 0.0005 | 0.0005 | -0.0000 |
| casual_loose_terms | cites expected | 0.00 | 0.25 | +0.25 |
| casual_loose_terms | correctness | 0.12 | 0.38 | +0.25 |
| casual_loose_terms | faithful | 0.80 | 0.83 | +0.03 |
| casual_loose_terms | p95 s | 3.5 | 5.1 | +1.58 |
| casual_loose_terms | retrieval hit | 0.25 | 0.50 | +0.25 |
| casual_multi_paper | $ per answer | 0.0007 | 0.0007 | +0.0000 |
| casual_multi_paper | cites expected | 1.00 | 1.00 | +0.00 |
| casual_multi_paper | correctness | 0.50 | 0.50 | +0.00 |
| casual_multi_paper | faithful | 0.67 | 0.67 | +0.00 |
| casual_multi_paper | p95 s | 4.4 | 5.3 | +0.96 |
| casual_multi_paper | retrieval hit | 1.00 | 1.00 | +0.00 |
| casual_typos | $ per answer | 0.0007 | 0.0008 | +0.0001 |
| casual_typos | cites expected | 1.00 | 1.00 | +0.00 |
| casual_typos | correctness | 0.67 | 0.83 | +0.17 |
| casual_typos | faithful | 0.67 | 0.67 | +0.00 |
| casual_typos | p95 s | 4.5 | 5.6 | +1.06 |
| casual_typos | retrieval hit | 1.00 | 1.00 | +0.00 |
| clinical_loose | $ per answer | 0.0008 | 0.0006 | -0.0002 |
| clinical_loose | cites expected | 1.00 | 1.00 | +0.00 |
| clinical_loose | correctness | 0.50 | 0.67 | +0.17 |
| clinical_loose | faithful | 1.00 | 0.67 | -0.33 |
| clinical_loose | p95 s | 5.6 | 6.5 | +0.94 |
| clinical_loose | retrieval hit | 1.00 | 1.00 | +0.00 |
| direct | $ per answer | 0.0005 | 0.0005 | +0.0000 |
| direct | cites expected | 1.00 | 1.00 | +0.00 |
| direct | correctness | 0.79 | 0.83 | +0.05 |
| direct | faithful | 0.86 | 0.86 | +0.00 |
| direct | p95 s | 6.6 | 6.8 | +0.13 |
| direct | retrieval hit | 1.00 | 1.00 | +0.00 |
| direct_computational | $ per answer | 0.0005 | 0.0006 | +0.0001 |
| direct_computational | cites expected | 1.00 | 1.00 | +0.00 |
| direct_computational | correctness | 1.00 | 1.00 | +0.00 |
| direct_computational | faithful | 0.67 | 1.00 | +0.33 |
| direct_computational | p95 s | 2.3 | 5.8 | +3.44 |
| direct_computational | retrieval hit | 1.00 | 1.00 | +0.00 |
| direct_human | $ per answer | 0.0006 | 0.0006 | +0.0000 |
| direct_human | cites expected | 1.00 | 1.00 | +0.00 |
| direct_human | correctness | 1.00 | 0.92 | -0.08 |
| direct_human | faithful | 0.67 | 0.67 | +0.00 |
| direct_human | p95 s | 3.9 | 7.4 | +3.44 |
| direct_human | retrieval hit | 1.00 | 1.00 | +0.00 |
| false_premise | $ per answer | 0.0006 | 0.0006 | +0.0000 |
| false_premise | cites expected | 1.00 | 1.00 | +0.00 |
| false_premise | correctness | 0.92 | 0.92 | +0.00 |
| false_premise | faithful | 0.83 | 0.83 | +0.00 |
| false_premise | p95 s | 3.5 | 4.3 | +0.81 |
| false_premise | retrieval hit | 1.00 | 1.00 | +0.00 |
| false_premise_casual | $ per answer | 0.0005 | 0.0006 | +0.0001 |
| false_premise_casual | cites expected | 1.00 | 1.00 | +0.00 |
| false_premise_casual | correctness | 0.50 | 0.83 | +0.33 |
| false_premise_casual | faithful | 0.33 | 1.00 | +0.67 |
| false_premise_casual | p95 s | 2.9 | 5.4 | +2.50 |
| false_premise_casual | retrieval hit | 1.00 | 1.00 | +0.00 |
| false_premise_keywords | $ per answer | 0.0005 | 0.0005 | +0.0001 |
| false_premise_keywords | cites expected | 1.00 | 1.00 | +0.00 |
| false_premise_keywords | correctness | 1.00 | 1.00 | +0.00 |
| false_premise_keywords | faithful | 1.00 | 0.67 | -0.33 |
| false_premise_keywords | p95 s | 3.1 | 3.7 | +0.58 |
| false_premise_keywords | retrieval hit | 1.00 | 1.00 | +0.00 |
| keywords | $ per answer | 0.0006 | 0.0007 | +0.0001 |
| keywords | cites expected | 1.00 | 1.00 | +0.00 |
| keywords | correctness | 1.00 | 1.00 | +0.00 |
| keywords | faithful | 0.67 | 0.67 | +0.00 |
| keywords | p95 s | 3.4 | 6.9 | +3.50 |
| keywords | retrieval hit | 1.00 | 1.00 | +0.00 |
| keywords_typos | $ per answer | 0.0007 | 0.0007 | +0.0000 |
| keywords_typos | cites expected | 1.00 | 1.00 | +0.00 |
| keywords_typos | correctness | 0.92 | 1.00 | +0.08 |
| keywords_typos | faithful | 0.83 | 1.00 | +0.17 |
| keywords_typos | p95 s | 4.2 | 4.6 | +0.41 |
| keywords_typos | retrieval hit | 1.00 | 1.00 | +0.00 |
| loose_terms | $ per answer | 0.0006 | 0.0006 | -0.0000 |
| loose_terms | cites expected | 1.00 | 0.83 | -0.17 |
| loose_terms | correctness | 1.00 | 0.67 | -0.33 |
| loose_terms | faithful | 1.00 | 1.00 | +0.00 |
| loose_terms | p95 s | 4.4 | 5.4 | +1.03 |
| loose_terms | retrieval hit | 1.00 | 1.00 | +0.00 |
| multi_paper | $ per answer | 0.0008 | 0.0008 | -0.0001 |
| multi_paper | cites expected | 1.00 | 1.00 | +0.00 |
| multi_paper | correctness | 0.58 | 0.75 | +0.17 |
| multi_paper | faithful | 0.83 | 1.00 | +0.17 |
| multi_paper | p95 s | 6.1 | 6.6 | +0.50 |
| multi_paper | retrieval hit | 1.00 | 1.00 | +0.00 |
| multilingual_ar | $ per answer | 0.0003 | 0.0002 | -0.0000 |
| multilingual_ar | cites expected | 0.00 | 0.00 | +0.00 |
| multilingual_ar | correctness | 0.00 | 0.00 | +0.00 |
| multilingual_ar | p95 s | 1.6 | 2.7 | +1.03 |
| multilingual_ar | retrieval hit | 0.00 | 0.00 | +0.00 |
| multilingual_de | $ per answer | 0.0004 | 0.0004 | +0.0000 |
| multilingual_de | cites expected | 0.00 | 0.00 | +0.00 |
| multilingual_de | correctness | 0.00 | 0.00 | +0.00 |
| multilingual_de | p95 s | 2.4 | 3.5 | +1.06 |
| multilingual_de | retrieval hit | 0.00 | 0.00 | +0.00 |
| multilingual_es | $ per answer | 0.0003 | 0.0004 | +0.0000 |
| multilingual_es | cites expected | 0.00 | 0.00 | +0.00 |
| multilingual_es | correctness | 0.00 | 0.00 | +0.00 |
| multilingual_es | p95 s | 1.6 | 3.5 | +1.90 |
| multilingual_es | retrieval hit | 0.00 | 0.00 | +0.00 |
| multilingual_fr | $ per answer | 0.0003 | 0.0003 | +0.0000 |
| multilingual_fr | cites expected | 0.00 | 0.00 | +0.00 |
| multilingual_fr | correctness | 0.00 | 0.00 | +0.00 |
| multilingual_fr | p95 s | 1.5 | 3.0 | +1.45 |
| multilingual_fr | retrieval hit | 0.00 | 0.00 | +0.00 |
| negative_result | $ per answer | 0.0006 | 0.0007 | +0.0000 |
| negative_result | cites expected | 1.00 | 1.00 | +0.00 |
| negative_result | correctness | 1.00 | 1.00 | +0.00 |
| negative_result | faithful | 0.67 | 0.33 | -0.33 |
| negative_result | p95 s | 3.3 | 5.5 | +2.16 |
| negative_result | retrieval hit | 1.00 | 1.00 | +0.00 |
| non_native_grammar | $ per answer | 0.0005 | 0.0005 | -0.0000 |
| non_native_grammar | cites expected | 1.00 | 1.00 | +0.00 |
| non_native_grammar | correctness | 1.00 | 1.00 | +0.00 |
| non_native_grammar | faithful | 1.00 | 1.00 | +0.00 |
| non_native_grammar | p95 s | 2.4 | 4.3 | +1.91 |
| non_native_grammar | retrieval hit | 1.00 | 1.00 | +0.00 |
| off_domain | $ per answer | 0.0003 | 0.0003 | +0.0000 |
| off_domain | not covered | 1.00 | 1.00 | +0.00 |
| off_domain | p95 s | 1.5 | 3.2 | +1.67 |
| off_domain_casual | $ per answer | 0.0003 | 0.0003 | +0.0000 |
| off_domain_casual | not covered | 1.00 | 1.00 | +0.00 |
| off_domain_casual | p95 s | 1.2 | 2.3 | +1.18 |
| out_of_corpus | $ per answer | 0.0002 | 0.0003 | +0.0000 |
| out_of_corpus | not covered | 1.00 | 1.00 | +0.00 |
| out_of_corpus | p95 s | 1.0 | 3.0 | +2.01 |
| out_of_corpus_casual | $ per answer | 0.0003 | 0.0003 | +0.0000 |
| out_of_corpus_casual | not covered | 1.00 | 1.00 | +0.00 |
| out_of_corpus_casual | p95 s | 1.3 | 3.0 | +1.64 |
| rambling_personal | $ per answer | 0.0007 | 0.0008 | +0.0001 |
| rambling_personal | cites expected | 1.00 | 1.00 | +0.00 |
| rambling_personal | correctness | 1.00 | 1.00 | +0.00 |
| rambling_personal | faithful | 1.00 | 0.67 | -0.33 |
| rambling_personal | p95 s | 4.7 | 8.2 | +3.50 |
| rambling_personal | retrieval hit | 1.00 | 1.00 | +0.00 |
| typos | $ per answer | 0.0007 | 0.0004 | -0.0003 |
| typos | cites expected | 0.67 | 0.00 | -0.67 |
| typos | correctness | 0.00 | 0.00 | +0.00 |
| typos | faithful | 0.67 | – | – |
| typos | p95 s | 4.8 | 3.3 | -1.54 |
| typos | retrieval hit | 0.67 | 0.00 | -0.67 |
