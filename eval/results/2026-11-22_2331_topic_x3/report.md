# Eval report: topic_x3

150 runs, 0 failed, 0 judge calls failed, $0.77 total

| questions | runs | correctness | faithful | paper@5 | page@5 | cites expected | not covered | cites papers | p50 s | p95 s | $ per run |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 150 | 0.77 | 0.95 | 0.89 | 0.72 | 0.89 | 1.00 | 0.11 | 2.9 | 4.8 | 0.0052 |
| borderline | 18 | – | 1.00 | – | – | – | – | 0.11 | 1.6 | 2.5 | 0.0026 |
| broad_vague | 3 | 0.00 | – | 0.00 | 0.00 | 0.00 | – | – | 2.1 | 2.2 | 0.0043 |
| casual | 9 | 0.56 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.5 | 4.1 | 0.0065 |
| casual_loose_terms | 12 | 0.58 | 1.00 | 0.50 | 0.50 | 0.50 | – | – | 3.5 | 5.2 | 0.0066 |
| casual_multi_paper | 3 | 0.50 | 1.00 | 1.00 | 0.00 | 1.00 | – | – | 4.5 | 4.9 | 0.0078 |
| casual_typos | 3 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.0 | 3.3 | 0.0064 |
| clinical_loose | 3 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.8 | 3.9 | 0.0069 |
| direct | 21 | 0.76 | 0.94 | 0.86 | 0.57 | 0.86 | – | – | 2.8 | 4.3 | 0.0061 |
| direct_computational | 3 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.3 | 3.4 | 0.0066 |
| direct_human | 6 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.5 | 3.7 | 0.0070 |
| false_premise | 6 | 1.00 | 0.83 | 1.00 | 0.50 | 1.00 | – | – | 2.5 | 3.1 | 0.0061 |
| false_premise_casual | 3 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.0 | 3.1 | 0.0063 |
| false_premise_keywords | 3 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.5 | 2.5 | 0.0058 |
| keywords | 3 | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 | – | – | 4.3 | 4.6 | 0.0070 |
| keywords_typos | 6 | 0.92 | 1.00 | 1.00 | 0.50 | 1.00 | – | – | 4.8 | 5.5 | 0.0077 |
| loose_terms | 6 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.8 | 4.2 | 0.0067 |
| multi_paper | 6 | 0.50 | 0.83 | 1.00 | 1.00 | 1.00 | – | – | 4.4 | 5.2 | 0.0080 |
| negative_result | 3 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.5 | 3.9 | 0.0069 |
| non_native_grammar | 3 | 1.00 | 0.33 | 1.00 | 1.00 | 1.00 | – | – | 3.0 | 3.3 | 0.0062 |
| off_domain | 15 | – | – | – | – | – | 1.00 | – | 0.3 | 2.4 | 0.0000 |
| off_domain_casual | 3 | – | – | – | – | – | 1.00 | – | 0.3 | 0.3 | 0.0000 |
| out_of_corpus | 3 | – | – | – | – | – | 1.00 | – | 1.6 | 1.7 | 0.0023 |
| out_of_corpus_casual | 3 | – | – | – | – | – | 1.00 | – | 2.0 | 2.1 | 0.0026 |
| rambling_personal | 3 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 4.6 | 4.8 | 0.0076 |
| typos | 3 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.8 | 2.8 | 0.0058 |

## Not correct

- q02 r1 partial: The answer correctly identifies that Ank2 deletion impairs remote memory while leaving recent memory intact, and correctly notes disruption of LTP maintenance, but omits the mechanistic details about reduced astrocyte contacts with engram neurons and impaired astrocyte morphogenesis through BDNF-TrkB.T1-IP3R2 signaling.
- q02 r2 partial: The answer correctly identifies that ankyrin-2 deletion impairs remote memory while leaving recent memory intact, and that it disrupts LTP maintenance, but misses the mechanistic details about reduced astrocyte-engram neuron contacts and the BDNF-TrkB.T1-IP3R2 signaling pathway underlying astrocyte morphogenesis.
- q02 r3 partial: The answer correctly identifies that Ank2 deletion impairs remote memory while sparing recent memory and disrupts LTP maintenance, but it omits the mechanistic details about reduced astrocyte contacts with engram neurons and impaired astrocyte morphogenesis via BDNF-TrkB.T1-IP3R2 signaling.
- q05 r1 partial: The answer correctly identifies the main findings that GHS-R1a elevation impairs memory formation by suppressing neuronal excitability, blocking memory allocation, hampering spatial coding, and reducing engram size, but it misses two key mechanisms mentioned in the reference: the role of LEAP2 (the endogenous antagonist) and chemogenetic rescue of the impairment by activating high-GHS-R1a neurons during training.
- q06 r1 wrong: The answer claims the documents don't contain relevant information, but the reference answer clearly demonstrates that research on this pathway has been conducted and shows it is selectively important for foraging-related spatial memory, not all spatial memory.
- q06 r2 wrong: The answer claims the papers don't contain information about this pathway, but the reference answer clearly describes specific findings about ventral hippocampus-lateral septum signaling and its selective role in appetitive spatial memory versus other types of spatial memory, indicating the papers do address this question.
- q06 r3 wrong: The answer claims the papers don't cover this topic, but the reference answer directly addresses the question with specific findings about which types of spatial memory the pathway supports and which it doesn't.
- q12 r1 wrong: The answer states claims about human studies improving memory and cognition through resistance training, but the reference answer explicitly states "The evidence in the corpus is from an animal model," indicating that human studies were not part of the reference corpus being evaluated.
- q12 r2 partial: The answer correctly states the rat study findings and IGF-1/IGF-1R increase, but the reference answer explicitly notes "The evidence in the corpus is from an animal model," indicating that human studies may not be covered in the corpus, yet the answer extensively discusses human studies which go beyond what the reference justifies.
- q12 r3 wrong: The answer contradicts the reference by claiming evidence from human studies, when the reference explicitly states "The evidence in the corpus is from an animal model" and only describes rat studies.
- q14 r1 partial: The answer correctly identifies that mice can form visuosocial memory from pictures and that they can distinguish conspecifics, but it does not mention the key mechanistic finding that PLCγ1 in hippocampal CA2 is required for this visuosocial preference memory, which is a main point of the reference answer.
- q14 r2 partial: The answer correctly identifies that mice have visuosocial memory and can form visual memories from pictures, but it omits the key mechanistic finding from the reference that this process requires PLCγ1 in hippocampal CA2.
- q14 r3 partial: The answer correctly confirms that mice can form visuosocial memories from pictures and mentions their ability to distinguish between conspecifics, but it fails to mention the critical mechanistic finding about PLCγ1 in hippocampal CA2 and the distinction between preference memory versus avoidance memory that the reference answer specifically highlights.
- q15 r1 partial: The answer correctly describes the circadian oscillation of MAPK and cAMP signaling in the hippocampus, the role of interference with these oscillations in impairing memory, and the dependence on the suprachiasmatic nucleus, but it notably omits the key finding that mice lacking the clock gene Bmal1 have impaired contextual fear and spatial memory, reduced Schaffer-collateral LTP, and lose training-induced Erk1/2 MAPK activation.
- q15 r2 partial: The answer correctly describes circadian oscillations of MAPK and cAMP, impairment from interfering with these oscillations, and the memory deficits in Bmal1-lacking mice including impaired contextual fear, spatial memory, and reduced LTP; however, it omits the key reference finding that training-induced Erk1/2 MAPK activation and the diurnal oscillation of these signaling molecules are lost in Bmal1-deficient mice.
- q15 r3 partial: The answer correctly identifies that MAPK and cAMP oscillate with circadian rhythm and that interfering with these oscillations impairs memory persistence, but it fails to mention key findings about Bmal1 knockout mice (impaired contextual fear and spatial memory, reduced Schaffer-collateral LTP, and loss of training-induced Erk1/2 MAPK activation), which are central to understanding how the circadian clock influences hippocampus-dependent memory.
- q16 r1 partial: The answer correctly identifies astrocytic TrkB.T1 signaling's role in enhancing remote memory and mentions PLCγ1 as a downstream BDNF pathway molecule, but it fails to specify that PLCγ1 is required for visuosocial preference memory in CA2 neurons, misses the connection to ankyrin-2 and astrocytic morphogenesis, and does not mention that BDNF signaling through IP3R2 is involved in memory persistence.
- q16 r2 partial: The answer correctly identifies key findings about astrocytic TrkB.T1 signaling, ankyrin-2 (Ank2), and PLCγ1 in memory persistence and remote memory, but omits the specific role of IP3R2 in astrocytes and fails to mention PLCγ1's requirement for visuosocial preference memory in CA2 neurons, missing an important cell-type-specific function described in the reference.
- q16 r3 partial: The answer correctly identifies PLCγ1's role in TrkB-mediated signaling and mentions astrocytic BDNF's importance for memory persistence, but it fails to specify the astrocyte-specific mechanisms (TrkB.T1, IP3R2, ankyrin-2 dependence) and does not mention CA2-specific visuosocial preference memory, missing key mechanistic details from the reference.
- q21 r1 partial: The answer correctly identifies that fast neutron irradiation causes object recognition memory deficits tested at 1 and 7 days post-irradiation and proposes reduced neurogenesis as a mechanism, but it contradicts the reference by claiming the effects are "temporary rather than permanent" when the reference provides no such information about permanence or temporality.
- q21 r2 partial: The answer correctly identifies the main findings—memory deficits in object recognition and fear conditioning, the timing (1 and 7 days post-irradiation), and the mechanism involving reduced neurogenesis markers (Ki-67, DCX)—but adds unsupported claims about the effects being "transient" and "temporary rather than permanent" that are not established in the reference answer.
- q21 r3 partial: The answer correctly identifies that neutron exposure causes memory deficits (object recognition memory, hippocampal involvement, neurogenesis reduction), but it contradicts the reference by claiming the effects are "temporary rather than permanent" when the reference only describes acute effects at 1 and 7 days post-irradiation without specifying permanence either way, and it omits contextual fear conditioning deficits mentioned in the reference.
- q25 r1 partial: The answer correctly captures that vmPFC plays an increasingly important role for older memories and that memories don't simply "move out" of the hippocampus, but it misses the key reference point that hippocampus still actively contributes to remote memory—emphasizing only that neural patterns change over time rather than explicitly stating the ongoing hippocampal involvement in remote memories.
- q25 r2 partial: The answer correctly describes the neural reorganization (changing hippocampal representation, increased vmPFC involvement) and appropriately qualifies this as "more nuanced than a simple move out," but it misses the key reference finding that the hippocampus still actively contributes to remote memory even after consolidation, contrary to the classic view.
- q25 r3 partial: The answer correctly describes the neural pattern changes within the hippocampus and vmPFC involvement in older memories, and appropriately notes the complexity beyond simple relocation, but it misses the reference's key point that newer rodent evidence shows the hippocampus still actively contributes to remote memories even after systems consolidation occurs.
- q28 r2 partial: The answer correctly identifies that the hippocampus is involved in both memory and bodily awareness and that these functions are linked, but it provides only general conceptual claims about embodied memory without citing the specific empirical finding from the reference answer—that hippocampal volume predicted both episodic memory performance and somatic awareness scores in mild cognitive impairment patients.
- q30 r1 partial: The answer correctly identifies the vmPFC's role in controlling whether memories are integrated or separated in the hippocampus, but fails to mention critical details from the reference: the dependence on spatial context, the specific timing requirement (7 days apart but not 5 hours), the mechanism through medial entorhinal cortex projections, and the role of neurogliaform inhibitory neurons in dorsal CA1.
- q30 r2 partial: The answer correctly identifies that vmPFC controls memory integration versus separation in the hippocampus, but misses critical details from the reference including the temporal spacing requirements (7 days vs 5 hours), the dependence on spatial context, the specific neural pathway through medial entorhinal cortex, and the role of neurogliaform inhibitory neurons in dorsal CA1.
- q30 r3 partial: The answer correctly identifies that vmPFC controls memory integration vs. separation in the hippocampus, but misses critical reference details including the role of spatial context, the specific 7-day vs. 5-hour timing distinction, and the documented mechanisms involving entorhinal cortex projections and neurogliaform inhibitory neurons in CA1.
- q31 r1 partial: The answer correctly identifies hippocampal mechanisms (specifically dentate gyrus) for separating similar memories but misses the neocortical GABA inhibition mechanism stated in the reference as a key protective mechanism against interference, and contradicts the reference by claiming these mechanisms remain "poorly understood" when the reference presents them as established findings.
- q31 r2 partial: The answer correctly identifies hippocampal mechanisms (specifically the dentate gyrus) for separating similar memories and provides supporting evidence about neural overlap, which aligns with the reference's mention of "hippocampus separates overlapping memories using relational information," but it completely misses the second major mechanism—the reference's finding about neocortical GABA inhibition protecting memories from interference and the specific evidence from brain stimulation experiments.
- q31 r3 partial: The answer correctly identifies hippocampal mechanisms for separating overlapping memories (specifically the dentate gyrus role in pattern separation), but it misses the reference's key finding about neocortical GABAergic inhibition as a protective mechanism against interference, which was demonstrated through brain stimulation experiments.
- q33 r1 wrong: The answer claims the documents don't address the question when the reference answer provides specific findings on this exact topic: anterior hippocampus for encoding and posterior hippocampus for retrieval of associative memory from stereo-EEG recordings.
- q33 r2 wrong: The answer claims the papers don't contain information about anterior versus posterior hippocampus during paired-associate memory retrieval, directly contradicting the reference answer which explicitly reports stereo-EEG findings on this exact comparison.
- q33 r3 wrong: The answer incorrectly claims the documents don't address the question when the reference answer clearly states that stereo-EEG recordings showed the rostral (anterior) hippocampus engages during encoding of associative memory and the caudal (posterior) hippocampus during retrieval.
- q35 r3 partial: The answer correctly identifies that Ythdf1 depletion impairs synaptic transmission and LTP in hippocampal neurons, and that it affects LTP-related proteins in the postsynaptic density, but misses the key mechanistic finding that Ythdf1 reads m6A marks and promotes stimulus-dependent translation of target mRNAs, which is the fundamental biological reason for these defects.
- q36 r1 wrong: The answer incorrectly claims the corpus doesn't address what determines memory persistence, when the reference answer explicitly identifies several key mechanisms (astrocytic ankyrin-2, BDNF/TrkB.T1 signaling, circadian oscillations of hippocampal MAPK/cAMP signaling, and CA1 place cell stabilization) that the corpus does cover.
- q36 r2 wrong: The answer states the corpus doesn't cover the question at all, but the reference indicates the corpus does cover relevant mechanisms including astrocytic ankyrin-2, BDNF/TrkB.T1 signaling, circadian oscillations of hippocampal MAPK/cAMP signaling, and CA1 place cell stability.
- q36 r3 wrong: The answer incorrectly states that the provided papers don't address the question, but the reference clearly indicates the corpus does cover relevant mechanisms including astrocytic ankyrin-2, BDNF/TrkB.T1 signaling, circadian oscillations of hippocampal signaling, and CA1 place cell stability that support memory persistence over time.

## Unfaithful

- q11 r2: "This suggests that cofilin overactivation affects memory probably in an AMPA receptor independent manner [3]."
- q16 r2: "BDNF is crucial for both recent and remote memory formation, with a particularly important role in supporting memory persistence through its activity around 12 hours after learning [2]."
- q18 r2: "procedural replay occurs independently of the hippocampus, indicating that replay-driven memory consolidation can operate through parallel, independent mechanisms"
- q24 r1: "working and reference memory of animals with unilateral lesions did not differ from animals with bilateral lesions and control animals"
- q24 r2: "Working and reference memory of animals with unilateral lesions did not differ from animals with bilateral lesions and control animals [2]"

## Loop

| kind | runs | declined | rewrites (mean) | web used | not covered |
|---|---|---|---|---|---|
| answer_from_corpus | 96 | 0 | 0.00 | 0 | 0 |
| correct_premise | 12 | 0 | 0.00 | 0 | 0 |
| decline | 18 | 18 | 0.00 | 0 | 0 |
| not_declined | 18 | 0 | 0.00 | 0 | 0 |
| web_fallback | 6 | 0 | 0.00 | 0 | 0 |

Paths:

- q01 answer_from_corpus: retrieve → generate
- q01 answer_from_corpus: retrieve → generate
- q01 answer_from_corpus: retrieve → generate
- q02 answer_from_corpus: retrieve → generate
- q02 answer_from_corpus: retrieve → generate
- q02 answer_from_corpus: retrieve → generate
- q03 answer_from_corpus: retrieve → generate
- q03 answer_from_corpus: retrieve → generate
- q03 answer_from_corpus: retrieve → generate
- q04 answer_from_corpus: retrieve → generate
- q04 answer_from_corpus: retrieve → generate
- q04 answer_from_corpus: retrieve → generate
- q05 answer_from_corpus: retrieve → generate
- q05 answer_from_corpus: retrieve → generate
- q05 answer_from_corpus: retrieve → generate
- q06 answer_from_corpus: retrieve → generate
- q06 answer_from_corpus: retrieve → generate
- q06 answer_from_corpus: retrieve → generate
- q07 answer_from_corpus: retrieve → generate
- q07 answer_from_corpus: retrieve → generate
- q07 answer_from_corpus: retrieve → generate
- q08 answer_from_corpus: retrieve → generate
- q08 answer_from_corpus: retrieve → generate
- q08 answer_from_corpus: retrieve → generate
- q09 answer_from_corpus: retrieve → generate
- q09 answer_from_corpus: retrieve → generate
- q09 answer_from_corpus: retrieve → generate
- q10 answer_from_corpus: retrieve → generate
- q10 answer_from_corpus: retrieve → generate
- q10 answer_from_corpus: retrieve → generate
- q11 answer_from_corpus: retrieve → generate
- q11 answer_from_corpus: retrieve → generate
- q11 answer_from_corpus: retrieve → generate
- q12 answer_from_corpus: retrieve → generate
- q12 answer_from_corpus: retrieve → generate
- q12 answer_from_corpus: retrieve → generate
- q13 answer_from_corpus: retrieve → generate
- q13 answer_from_corpus: retrieve → generate
- q13 answer_from_corpus: retrieve → generate
- q14 answer_from_corpus: retrieve → generate
- q14 answer_from_corpus: retrieve → generate
- q14 answer_from_corpus: retrieve → generate
- q15 answer_from_corpus: retrieve → generate
- q15 answer_from_corpus: retrieve → generate
- q15 answer_from_corpus: retrieve → generate
- q16 answer_from_corpus: retrieve → generate
- q16 answer_from_corpus: retrieve → generate
- q16 answer_from_corpus: retrieve → generate
- q17 correct_premise: retrieve → generate
- q17 correct_premise: retrieve → generate
- q17 correct_premise: retrieve → generate
- q18 correct_premise: retrieve → generate
- q18 correct_premise: retrieve → generate
- q18 correct_premise: retrieve → generate
- q19 web_fallback: retrieve → generate
- q19 web_fallback: retrieve → generate
- q19 web_fallback: retrieve → generate
- q20 decline: declined
- q20 decline: declined
- q20 decline: declined
- q21 answer_from_corpus: retrieve → generate
- q21 answer_from_corpus: retrieve → generate
- q21 answer_from_corpus: retrieve → generate
- q22 answer_from_corpus: retrieve → generate
- q22 answer_from_corpus: retrieve → generate
- q22 answer_from_corpus: retrieve → generate
- q23 answer_from_corpus: retrieve → generate
- q23 answer_from_corpus: retrieve → generate
- q23 answer_from_corpus: retrieve → generate
- q24 answer_from_corpus: retrieve → generate
- q24 answer_from_corpus: retrieve → generate
- q24 answer_from_corpus: retrieve → generate
- q25 answer_from_corpus: retrieve → generate
- q25 answer_from_corpus: retrieve → generate
- q25 answer_from_corpus: retrieve → generate
- q26 answer_from_corpus: retrieve → generate
- q26 answer_from_corpus: retrieve → generate
- q26 answer_from_corpus: retrieve → generate
- q27 answer_from_corpus: retrieve → generate
- q27 answer_from_corpus: retrieve → generate
- q27 answer_from_corpus: retrieve → generate
- q28 answer_from_corpus: retrieve → generate
- q28 answer_from_corpus: retrieve → generate
- q28 answer_from_corpus: retrieve → generate
- q29 answer_from_corpus: retrieve → generate
- q29 answer_from_corpus: retrieve → generate
- q29 answer_from_corpus: retrieve → generate
- q30 answer_from_corpus: retrieve → generate
- q30 answer_from_corpus: retrieve → generate
- q30 answer_from_corpus: retrieve → generate
- q31 answer_from_corpus: retrieve → generate
- q31 answer_from_corpus: retrieve → generate
- q31 answer_from_corpus: retrieve → generate
- q32 answer_from_corpus: retrieve → generate
- q32 answer_from_corpus: retrieve → generate
- q32 answer_from_corpus: retrieve → generate
- q33 answer_from_corpus: retrieve → generate
- q33 answer_from_corpus: retrieve → generate
- q33 answer_from_corpus: retrieve → generate
- q34 answer_from_corpus: retrieve → generate
- q34 answer_from_corpus: retrieve → generate
- q34 answer_from_corpus: retrieve → generate
- q35 answer_from_corpus: retrieve → generate
- q35 answer_from_corpus: retrieve → generate
- q35 answer_from_corpus: retrieve → generate
- q36 answer_from_corpus: retrieve → generate
- q36 answer_from_corpus: retrieve → generate
- q36 answer_from_corpus: retrieve → generate
- q41 correct_premise: retrieve → generate
- q41 correct_premise: retrieve → generate
- q41 correct_premise: retrieve → generate
- q42 correct_premise: retrieve → generate
- q42 correct_premise: retrieve → generate
- q42 correct_premise: retrieve → generate
- q43 web_fallback: retrieve → generate
- q43 web_fallback: retrieve → generate
- q43 web_fallback: retrieve → generate
- q44 decline: declined
- q44 decline: declined
- q44 decline: declined
- q45 not_declined: retrieve → generate
- q45 not_declined: retrieve → generate
- q45 not_declined: retrieve → generate
- q46 not_declined: retrieve → generate
- q46 not_declined: retrieve → generate
- q46 not_declined: retrieve → generate
- q47 not_declined: retrieve → generate
- q47 not_declined: retrieve → generate
- q47 not_declined: retrieve → generate
- q48 not_declined: retrieve → generate
- q48 not_declined: retrieve → generate
- q48 not_declined: retrieve → generate
- q49 not_declined: retrieve → generate
- q49 not_declined: retrieve → generate
- q49 not_declined: retrieve → generate
- q50 not_declined: retrieve → generate
- q50 not_declined: retrieve → generate
- q50 not_declined: retrieve → generate
- q51 decline: declined
- q51 decline: declined
- q51 decline: declined
- q52 decline: declined
- q52 decline: declined
- q52 decline: declined
- q53 decline: declined
- q53 decline: declined
- q53 decline: declined
- q54 decline: declined
- q54 decline: declined
- q54 decline: declined
