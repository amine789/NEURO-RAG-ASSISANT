# Eval report: deployed

50 runs, 0 failed, 0 judge calls failed, $0.26 total

| questions | runs | correctness | faithful | paper@5 | page@5 | cites expected | not covered | cites papers | p50 s | p95 s | $ per run |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 50 | 0.68 | 0.91 | 0.89 | 0.67 | 0.86 | 1.00 | 0.17 | 2.0 | 3.9 | 0.0052 |
| borderline | 6 | – | 1.00 | – | – | – | – | 0.17 | 1.1 | 2.4 | 0.0028 |
| broad_vague | 1 | 0.00 | – | 0.00 | 0.00 | 0.00 | – | – | 1.0 | 1.0 | 0.0040 |
| casual | 3 | 0.33 | 1.00 | 0.67 | 0.33 | 0.67 | – | – | 1.9 | 2.7 | 0.0053 |
| casual_loose_terms | 4 | 0.62 | 1.00 | 0.75 | 0.50 | 0.50 | – | – | 1.5 | 4.0 | 0.0057 |
| casual_multi_paper | 1 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.5 | 3.5 | 0.0074 |
| casual_typos | 1 | 0.00 | 1.00 | 1.00 | 0.00 | 1.00 | – | – | 2.2 | 2.2 | 0.0060 |
| clinical_loose | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.1 | 3.1 | 0.0066 |
| direct | 7 | 0.57 | 0.67 | 0.86 | 0.43 | 0.86 | – | – | 2.0 | 3.8 | 0.0059 |
| direct_computational | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.2 | 2.2 | 0.0065 |
| direct_human | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.0 | 3.8 | 0.0076 |
| false_premise | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.1 | 2.8 | 0.0064 |
| false_premise_casual | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 1.9 | 1.9 | 0.0061 |
| false_premise_keywords | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 1.8 | 1.8 | 0.0057 |
| keywords | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.7 | 2.7 | 0.0061 |
| keywords_typos | 2 | 0.75 | 1.00 | 1.00 | 0.50 | 1.00 | – | – | 2.5 | 3.2 | 0.0070 |
| loose_terms | 2 | 0.75 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.6 | 3.4 | 0.0068 |
| multi_paper | 2 | 0.75 | 1.00 | 1.00 | 0.50 | 1.00 | – | – | 3.2 | 3.9 | 0.0079 |
| negative_result | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.9 | 2.9 | 0.0065 |
| non_native_grammar | 1 | 0.50 | 0.00 | 1.00 | 1.00 | 1.00 | – | – | 2.5 | 2.5 | 0.0063 |
| off_domain | 5 | – | – | – | – | – | 1.00 | – | 1.2 | 1.3 | 0.0023 |
| off_domain_casual | 1 | – | – | – | – | – | 1.00 | – | 1.5 | 1.5 | 0.0022 |
| out_of_corpus | 1 | – | – | – | – | – | 1.00 | – | 1.2 | 1.2 | 0.0022 |
| out_of_corpus_casual | 1 | – | – | – | – | – | 1.00 | – | 1.6 | 1.6 | 0.0024 |
| rambling_personal | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 4.0 | 4.0 | 0.0072 |
| typos | 1 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 1.9 | 1.9 | 0.0057 |

## Not correct

- q02 r1 partial: The answer correctly states that ankyrin-2 deletion impairs remote memory while leaving recent memory intact, but it omits key mechanisms mentioned in the reference: disruption of LTP maintenance, reduced astrocyte contacts with engram neurons, and impaired astrocyte morphogenesis driven by BDNF signaling through TrkB.T1 and IP3R2.
- q04 r1 partial: The answer correctly identifies that presynaptic Rac1 inhibition selectively impairs spatial working memory, but it states that postsynaptic Rac1 inhibition impairs "remote memory" specifically, whereas the reference states it affects "longer-term cognitive processes" more broadly, making the postsynaptic claim too narrow and potentially inconsistent with the reference's broader characterization.
- q05 r1 partial: The answer correctly identifies that GHS-R1a expression in dCA1 impairs memory encoding and mentions engram size regulation, but it focuses on ghrelin/agonist administration rather than the key finding about elevated GHS-R1a expression itself, omits the suppression of neuronal excitability and memory allocation, and misses the rescue by LEAP2 and chemogenetic activation that are central to understanding the mechanism.
- q06 r1 wrong: The answer claims the papers don't cover this topic, but the reference answer directly addresses the question with specific empirical findings about which types of spatial memory this pathway does and does not support.
- q11 r1 partial: The answer correctly identifies that cofilin overactivation improves short-term memory in the object-location task, but it misses the key finding that this occurs without affecting AMPA receptor expression levels, and omits the information about anxiety-like behavior and the suggestion about benefits to short-term plasticity.
- q12 r1 wrong: The answer claims the papers don't cover the relationship between lifting weights and memory, but the reference answer explicitly describes a study showing resistance exercise improved memory performance in an animal model, contradicting this assessment.
- q14 r1 wrong: The answer states that "the specific question of whether they can recognize and remember individual mice from photographs is not addressed in these documents," which contradicts the reference answer that explicitly states "Yes" and describes portrait pictures as a research method used to demonstrate this ability.
- q16 r1 partial: The answer correctly identifies PLCγ1 as a downstream BDNF signaling molecule and mentions astrocyte morphogenesis and memory persistence, but misses critical mechanistic details from the reference: specifically that TrkB.T1 (not just TrkB generally) and IP3R2 drive the astrocytic morphogenesis, that ankyrin-2 supports this process, that optogenetic activation of astrocytic TrkB.T1 enhances remote memory, and that PLCγ1's role in CA2 neurons is specifically for visuosocial preference memory.
- q21 r1 wrong: The answer claims the specific memory results are not included in the document excerpts, but the reference answer clearly states the results showing significant deficits in object recognition memory and contextual fear conditioning, contradicting the claim that the information is unavailable.
- q23 r1 wrong: The answer claims the papers don't address this question, but the reference answer clearly describes preclinical findings showing a PDE1 inhibitor improved memory when given immediately after training, which directly addresses the question about taking something after studying to improve retention.
- q24 r1 partial: The answer correctly identifies that bilateral hippocampal lesions from vincristine impair working and reference memory, and that unilateral lesions do not impair memory, but it mischaracterizes the unilateral lesion comparison by stating they "did not differ from animals with bilateral lesions," when the reference states they did not differ from either controls or bilateral lesion rats (implying they were more similar to controls and different from bilateral lesion rats).
- q25 r1 partial: The answer correctly describes the classical systems-consolidation theory and mentions human findings about memory reorganization over time, but it misses the key reference finding that older memories show comparable vmPFC and hippocampal involvement (not just hippocampal-to-cortical transfer), and importantly fails to mention the newer rodent evidence showing the hippocampus continues to actively contribute to remote memories despite classic theory predictions.
- q26 r1 partial: The answer correctly captures the main findings about increasing place cell stability over days, the role of BTSP in re-forming place cells daily, and the CA1 localization, but it does not mention that stable cells over-represented task-relevant information or correlated with performance, which is a key reference finding.
- q30 r1 partial: The answer correctly identifies that the ventromedial prefrontal cortex controls memory integration versus separation in the hippocampus, but misses critical details from the reference including the importance of spatial context, the specific 7-day temporal threshold, the role of medial entorhinal cortex projections, and neurogliaform cell involvement.
- q31 r1 partial: The answer correctly identifies the hippocampus (specifically the dentate gyrus) and relational/contextual information as separating overlapping memories, but it misses the reference's second main finding about neocortical GABAergic inhibition as a protective mechanism against memory interference.
- q35 r1 partial: The answer correctly describes the behavioral learning deficits in Ythdf1-KO mice but fails to identify the key mechanistic findings (impaired synaptic transmission, reduced LTP, and defects in m6A-dependent translation in hippocampal neurons) that explain why these learning problems occur.
- q36 r1 wrong: The answer incorrectly claims the corpus doesn't cover the topic, when the reference indicates the papers do address relevant mechanisms including astrocytic ankyrin-2, BDNF/TrkB.T1 signaling, circadian MAPK/cAMP oscillations, and CA1 place cell stability that support memory persistence.

## Unfaithful

- q01 r1: "LTP (long-term potentiation) is a form of synaptic plasticity thought to underlie memory storage."
- q05 r1: "An engram is the physical neural substrate that stores memory information."
- q24 r1: "Working and reference memory of animals with unilateral lesions did not differ from animals with bilateral lesions and control animals [2]."
