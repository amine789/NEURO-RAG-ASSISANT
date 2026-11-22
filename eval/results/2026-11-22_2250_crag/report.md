# Eval report: crag

50 runs, 0 failed, 0 judge calls failed, $0.23 total

| questions | runs | correctness | faithful | paper@5 | page@5 | cites expected | not covered | cites papers | p50 s | p95 s | $ per run |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 50 | 0.75 | 0.97 | 0.89 | 0.75 | 0.89 | 1.00 | 0.00 | 4.3 | 14.7 | 0.0047 |
| borderline | 6 | – | – | – | – | – | – | 0.00 | 12.0 | 15.8 | 0.0004 |
| broad_vague | 1 | 0.00 | – | 0.00 | 0.00 | 0.00 | – | – | 3.5 | 3.5 | 0.0040 |
| casual | 3 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.8 | 4.3 | 0.0066 |
| casual_loose_terms | 4 | 0.75 | 1.00 | 0.75 | 0.75 | 0.75 | – | – | 4.0 | 5.1 | 0.0066 |
| casual_multi_paper | 1 | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 | – | – | 4.3 | 4.3 | 0.0076 |
| casual_typos | 1 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.2 | 3.2 | 0.0062 |
| clinical_loose | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 4.3 | 4.3 | 0.0072 |
| direct | 7 | 0.86 | 1.00 | 1.00 | 0.71 | 1.00 | – | – | 3.3 | 4.9 | 0.0064 |
| direct_computational | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.4 | 3.4 | 0.0066 |
| direct_human | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.8 | 4.7 | 0.0070 |
| false_premise | 2 | 0.50 | 1.00 | 0.50 | 0.50 | 0.50 | – | – | 4.9 | 15.7 | 0.0037 |
| false_premise_casual | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.8 | 2.8 | 0.0063 |
| false_premise_keywords | 1 | 0.00 | – | 0.00 | 0.00 | 0.00 | – | – | 11.8 | 11.8 | 0.0013 |
| keywords | 1 | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 | – | – | 4.2 | 4.2 | 0.0067 |
| keywords_typos | 2 | 0.75 | 1.00 | 1.00 | 0.50 | 1.00 | – | – | 4.9 | 4.9 | 0.0079 |
| loose_terms | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 4.4 | 4.7 | 0.0070 |
| multi_paper | 2 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 5.1 | 5.1 | 0.0082 |
| negative_result | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 4.0 | 4.0 | 0.0069 |
| non_native_grammar | 1 | 1.00 | 0.00 | 1.00 | 1.00 | 1.00 | – | – | 3.7 | 3.7 | 0.0065 |
| off_domain | 5 | – | – | – | – | – | 1.00 | – | 0.3 | 0.3 | 0.0000 |
| off_domain_casual | 1 | – | – | – | – | – | 1.00 | – | 0.4 | 0.4 | 0.0000 |
| out_of_corpus | 1 | – | – | – | – | – | 1.00 | – | 12.8 | 12.8 | 0.0000 |
| out_of_corpus_casual | 1 | – | – | – | – | – | 1.00 | – | 11.1 | 11.1 | 0.0000 |
| rambling_personal | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 5.1 | 5.1 | 0.0076 |
| typos | 1 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.0 | 3.0 | 0.0058 |

## Not correct

- q02 r1 partial: The answer correctly identifies that ankyrin-2 deletion impairs remote memory while leaving recent memory intact and disrupts LTP maintenance, but it misses the mechanistic details about reduced astrocyte contacts with engram neurons and the impaired astrocyte morphogenesis driven by BDNF signaling through TrkB.T1 and IP3R2.
- q05 r1 partial: The answer correctly describes that GHS-R1a elevation impairs memory formation by suppressing excitability, blocking memory allocation, hampering spatial coding, and reducing engram size, but it omits key information about LEAP2's role as the endogenous antagonist and misrepresents the rescue mechanism—chemogenetic activation of high-GHS-R1a neurons during training rescues the impairment, rather than antagonizing GHS-R1a activity during training.
- q12 r1 wrong: The answer contradicts the reference by claiming evidence from human studies, when the reference explicitly states "The evidence in the corpus is from an animal model" and only describes rat findings.
- q14 r1 partial: The answer correctly states that mice can form visuosocial memories and can associate mouse photos with valenced outcomes, but it misses the key reference finding that this requires PLCγ1 in hippocampal CA2 and that avoidance memory does not require this molecule.
- q15 r1 partial: The answer correctly identifies MAPK and cAMP oscillations, interference with these oscillations impairing memory persistence, and the memory deficits in Bmal1-knockout mice with reduced LTP, but it omits the specific finding that training-induced Erk1/2 MAPK activation and the diurnal oscillation of MAPK and cAMP are lost in Bmal1-deficient mice.
- q16 r1 partial: The answer correctly identifies key mechanisms (TrkB.T1 signaling in astrocytes, PLCγ1 in BDNF pathway, optogenetic activation enhancing remote memory, and ankyrin-2's role in memory persistence) that align with the reference, but omits the critical detail about PLCγ1's specific requirement for visuosocial preference memory in CA2 neurons, which is a main finding in the reference answer.
- q17 r1 wrong: The answer says the papers don't cover the topic, but according to the reference, the papers do address this question by showing that the premise is incorrect—CPEB4 knockout mice actually have normal hippocampus-related plasticity and memory—and a good answer should correct this false premise rather than claim the papers don't cover it.
- q21 r1 partial: The answer correctly identifies object recognition memory deficits at 1 and 7 days post-irradiation and the connection to reduced hippocampal neurogenesis, but it misses the reference's finding regarding contextual fear conditioning deficits and incorrectly suggests the effects are temporary/transient when the reference does not make this claim.
- q28 r1 partial: The answer correctly captures that the hippocampus links memory and bodily awareness (embodiment/bodily selfhood), but lacks the specific empirical evidence from the reference about hippocampal volume predicting both episodic memory and somatic awareness in mild cognitive impairment patients, and does not mention the control region comparison that strengthens the finding.
- q30 r1 partial: The answer correctly identifies the vmPFC's role in controlling memory integration versus separation in the hippocampus, but misses key mechanistic details provided in the reference: the dependence on spatial context, the specific timing requirement (7 days vs 5 hours apart), the vmPFC's projections to medial entorhinal cortex, and the involvement of neurogliaform inhibitory neurons in dorsal CA1.
- q31 r1 partial: The answer correctly identifies hippocampal mechanisms (specifically the dentate gyrus) for separating similar memories and mentions overlap reduction, but fails to address the key neocortical GABAergic inhibition mechanism that the reference identifies as central to preventing memory interference, and notably concludes that underlying mechanisms are "poorly understood" when the reference explicitly describes them as identified.
- q35 r1 partial: The answer correctly identifies that YTHDF1 KO impairs LTP and synaptic transmission leading to learning deficits, but it omits the critical reference detail that YTHDF1 reads m6A marks and promotes stimulus-dependent translation of target mRNAs, which is the mechanistic basis for these effects.
- q36 r1 wrong: The answer incorrectly states that the corpus doesn't address memory durability, when the reference indicates the papers do cover relevant mechanisms including astrocytic ankyrin-2, BDNF/TrkB.T1 signaling, circadian MAPK/cAMP oscillations, and CA1 place cell stability that support memory persistence.
- q42 r1 wrong: The answer claims the papers don't cover PDE1B and memory, but the reference answer directly states that the papers show blocking PDE1B actually enhances memory rather than worsens it, contradicting the question's premise.

## Unfaithful

- q24 r1: "working and reference memory of animals with unilateral lesions did not differ from animals with bilateral lesions and control animals"

## Loop

| kind | runs | declined | rewrites (mean) | web used | not covered |
|---|---|---|---|---|---|
| answer_from_corpus | 32 | 0 | 0.09 | 0 | 0 |
| correct_premise | 4 | 0 | 1.25 | 0 | 2 |
| decline | 6 | 6 | 0.00 | 0 | 0 |
| not_declined | 6 | 0 | 1.67 | 0 | 5 |
| web_fallback | 2 | 0 | 2.00 | 0 | 2 |

Paths:

- q01 answer_from_corpus: retrieve → grade:good → generate
- q02 answer_from_corpus: retrieve → grade:good → generate
- q03 answer_from_corpus: retrieve → grade:good → generate
- q04 answer_from_corpus: retrieve → grade:good → generate
- q05 answer_from_corpus: retrieve → grade:good → generate
- q06 answer_from_corpus: retrieve → grade:weak → rewrite → retrieve → grade:good → generate
- q07 answer_from_corpus: retrieve → grade:good → generate
- q08 answer_from_corpus: retrieve → grade:good → generate
- q09 answer_from_corpus: retrieve → grade:good → generate
- q10 answer_from_corpus: retrieve → grade:good → generate
- q11 answer_from_corpus: retrieve → grade:good → generate
- q12 answer_from_corpus: retrieve → grade:good → generate
- q13 answer_from_corpus: retrieve → grade:good → generate
- q14 answer_from_corpus: retrieve → grade:good → generate
- q15 answer_from_corpus: retrieve → grade:good → generate
- q16 answer_from_corpus: retrieve → grade:good → generate
- q17 correct_premise: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:weak → not_covered
- q18 correct_premise: retrieve → grade:weak → rewrite → retrieve → grade:good → generate
- q19 web_fallback: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:weak → not_covered
- q20 decline: declined
- q21 answer_from_corpus: retrieve → grade:good → generate
- q22 answer_from_corpus: retrieve → grade:good → generate
- q23 answer_from_corpus: retrieve → grade:good → generate
- q24 answer_from_corpus: retrieve → grade:good → generate
- q25 answer_from_corpus: retrieve → grade:good → generate
- q26 answer_from_corpus: retrieve → grade:good → generate
- q27 answer_from_corpus: retrieve → grade:good → generate
- q28 answer_from_corpus: retrieve → grade:good → generate
- q29 answer_from_corpus: retrieve → grade:good → generate
- q30 answer_from_corpus: retrieve → grade:good → generate
- q31 answer_from_corpus: retrieve → grade:good → generate
- q32 answer_from_corpus: retrieve → grade:good → generate
- q33 answer_from_corpus: retrieve → grade:weak → rewrite → retrieve → grade:good → generate
- q34 answer_from_corpus: retrieve → grade:good → generate
- q35 answer_from_corpus: retrieve → grade:good → generate
- q36 answer_from_corpus: retrieve → grade:weak → rewrite → retrieve → grade:good → generate
- q41 correct_premise: retrieve → grade:good → generate
- q42 correct_premise: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:weak → not_covered
- q43 web_fallback: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:weak → not_covered
- q44 decline: declined
- q45 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:weak → not_covered
- q46 not_declined: retrieve → grade:good → generate
- q47 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:weak → not_covered
- q48 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:weak → not_covered
- q49 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:weak → not_covered
- q50 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:weak → not_covered
- q51 decline: declined
- q52 decline: declined
- q53 decline: declined
- q54 decline: declined
