# Eval report: rerank

50 runs, 0 failed, 0 judge calls failed, $0.27 total

| questions | runs | correctness | faithful | paper@5 | page@5 | cites expected | not covered | cites papers | p50 s | p95 s | $ per run |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 50 | 0.78 | 0.97 | 0.89 | 0.72 | 0.86 | 1.00 | 0.17 | 2.5 | 4.4 | 0.0054 |
| borderline | 6 | – | 1.00 | – | – | – | – | 0.17 | 1.4 | 2.2 | 0.0027 |
| broad_vague | 1 | 0.00 | – | 0.00 | 0.00 | 0.00 | – | – | 2.6 | 2.6 | 0.0045 |
| casual | 3 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.8 | 3.1 | 0.0064 |
| casual_loose_terms | 4 | 0.62 | 1.00 | 0.50 | 0.50 | 0.50 | – | – | 3.3 | 4.4 | 0.0067 |
| casual_multi_paper | 1 | 0.50 | 1.00 | 1.00 | 0.00 | 1.00 | – | – | 3.3 | 3.3 | 0.0075 |
| casual_typos | 1 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.6 | 2.6 | 0.0062 |
| clinical_loose | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.4 | 3.4 | 0.0068 |
| direct | 7 | 0.86 | 1.00 | 0.86 | 0.57 | 0.86 | – | – | 2.5 | 4.7 | 0.0061 |
| direct_computational | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.4 | 2.4 | 0.0064 |
| direct_human | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.0 | 3.7 | 0.0070 |
| false_premise | 2 | 1.00 | 1.00 | 1.00 | 0.50 | 0.50 | – | – | 1.3 | 2.5 | 0.0052 |
| false_premise_casual | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.5 | 2.5 | 0.0063 |
| false_premise_keywords | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.4 | 2.4 | 0.0058 |
| keywords | 1 | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 | – | – | 3.9 | 3.9 | 0.0072 |
| keywords_typos | 2 | 0.75 | 1.00 | 1.00 | 0.50 | 1.00 | – | – | 3.7 | 4.3 | 0.0078 |
| loose_terms | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.5 | 4.1 | 0.0066 |
| multi_paper | 2 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.5 | 4.2 | 0.0079 |
| negative_result | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.6 | 2.6 | 0.0062 |
| non_native_grammar | 1 | 1.00 | 0.00 | 1.00 | 1.00 | 1.00 | – | – | 2.9 | 2.9 | 0.0062 |
| off_domain | 5 | – | – | – | – | – | 1.00 | – | 1.5 | 6.6 | 0.0026 |
| off_domain_casual | 1 | – | – | – | – | – | 1.00 | – | 1.4 | 1.4 | 0.0026 |
| out_of_corpus | 1 | – | – | – | – | – | 1.00 | – | 1.5 | 1.5 | 0.0023 |
| out_of_corpus_casual | 1 | – | – | – | – | – | 1.00 | – | 1.5 | 1.5 | 0.0025 |
| rambling_personal | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 4.2 | 4.2 | 0.0079 |
| typos | 1 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.2 | 2.2 | 0.0059 |

## Not correct

- q06 r1 wrong: The answer claims the papers don't cover this question, but the reference answer demonstrates that the papers clearly do address which types of spatial memory depend on the ventral hippocampus-to-lateral septum pathway, showing it is needed for appetitive spatial memory but not aversive or other learning types.
- q12 r1 wrong: The answer contradicts the reference by claiming human studies demonstrate that resistance training improves memory and cognition with increased IGF-1, when the reference explicitly states "The evidence in the corpus is from an animal model" - indicating no human studies are covered in the source material.
- q14 r1 partial: The answer correctly states that mice have visuosocial memory and can form memories from photographs, but it focuses on conditioned fear and reward associations rather than the reference's key finding that mice can distinguish conspecifics from other species through visuosocial memory, and it completely omits the mechanistic finding about PLCγ1 in hippocampal CA2.
- q15 r1 partial: The answer correctly identifies that hippocampal MAPK and cAMP signaling oscillate circadianly and that interfering with these oscillations impairs memory persistence, and mentions the importance of the SCN; however, it does not address the key reference finding about Bmal1-deficient mice having impaired contextual fear and spatial memory, reduced Schaffer-collateral LTP, and loss of training-induced Erk1/2 MAPK activation.
- q16 r1 partial: The answer correctly identifies that astrocytic TrkB.T1 signaling enhances remote memory and that PLCγ1 is involved in BDNF signaling, but it misses the specific reference answer details that this pathway depends on ankyrin-2, that IP3R2 is involved in astrocytic signaling, that the morphogenesis mechanism supports memory persistence, and that PLCγ1 is specifically required for visuosocial preference memory in CA2 neurons rather than just general LTP in CA1.
- q21 r1 partial: The answer correctly identifies object recognition memory deficits at 1 and 7 days post-irradiation and the connection to reduced neurogenesis, but it adds an unsupported claim that the effects are "temporary rather than permanent" that contradicts or goes beyond the reference's findings, and it omits the reference's finding about contextual fear conditioning deficits.
- q25 r1 partial: The answer correctly describes hippocampal representational changes over time and vmPFC involvement in older memories, but critically omits the reference's key point that the hippocampus continues to actively contribute to remote memory retrieval despite the systems-consolidation theory, as evidenced by rodent lesion studies showing post-learning hippocampal damage impairs remote memory.
- q30 r1 partial: The answer correctly identifies that the ventromedial prefrontal cortex controls memory integration versus separation in the hippocampus, but misses critical details from the reference including the temporal spacing requirement (7 days vs. 5 hours), the spatial context dependency, the direct projections to medial entorhinal cortex, and the role of neurogliaform inhibitory neurons in dorsal CA1.
- q31 r1 partial: The answer correctly identifies the hippocampus (specifically the dentate gyrus) as separating overlapping memories using contextual/relational information, which aligns with the reference, but completely omits the second key mechanism: neocortical GABAergic inhibition and its protective role against memory interference, which the reference identifies as equally important.
- q33 r1 wrong: The answer states the documents don't contain information about anterior versus posterior hippocampus processing of paired-associate memories, contradicting the reference answer which provides specific findings about rostral hippocampus during encoding and caudal hippocampus during retrieval for associative memory.
- q35 r1 partial: The answer correctly identifies that Ythdf1 KO impairs synaptic transmission, LTP, and learning, but crucially omits the reference's key mechanistic finding that Ythdf1 reads m6A marks and promotes stimulus-dependent translation of target mRNAs, which is the fundamental explanation for why protein synthesis and synaptic function are affected.
- q36 r1 wrong: The answer claims the papers don't address the question at all, but the reference indicates the corpus does cover relevant mechanisms (astrocytic ankyrin-2, BDNF/TrkB.T1 signaling, circadian MAPK/cAMP oscillations, and CA1 place cell stability) that support memory persistence over weeks.

## Unfaithful

- q24 r1: "Working and reference memory of animals with unilateral lesions did not differ from animals with bilateral lesions"
