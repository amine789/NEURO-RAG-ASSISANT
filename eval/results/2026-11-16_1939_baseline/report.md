# Eval report: baseline

50 runs, 0 failed, 0 judge calls failed, $0.26 total

| questions | runs | correctness | faithful | paper@5 | page@5 | cites expected | not covered | cites papers | p50 s | p95 s | $ per run |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 50 | 0.67 | 0.97 | 0.89 | 0.67 | 0.86 | 1.00 | 0.00 | 1.7 | 3.9 | 0.0052 |
| borderline | 6 | – | – | – | – | – | – | 0.00 | 0.9 | 1.2 | 0.0024 |
| broad_vague | 1 | 0.00 | – | 0.00 | 0.00 | 0.00 | – | – | 1.3 | 1.3 | 0.0043 |
| casual | 3 | 0.33 | 1.00 | 0.67 | 0.33 | 0.67 | – | – | 2.2 | 2.6 | 0.0054 |
| casual_loose_terms | 4 | 0.38 | 1.00 | 0.75 | 0.50 | 0.50 | – | – | 1.7 | 3.9 | 0.0058 |
| casual_multi_paper | 1 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.5 | 3.5 | 0.0074 |
| casual_typos | 1 | 0.00 | 1.00 | 1.00 | 0.00 | 1.00 | – | – | 1.9 | 1.9 | 0.0061 |
| clinical_loose | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.8 | 2.8 | 0.0066 |
| direct | 7 | 0.50 | 1.00 | 0.86 | 0.43 | 0.86 | – | – | 1.7 | 2.5 | 0.0058 |
| direct_computational | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 1.6 | 1.6 | 0.0062 |
| direct_human | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.5 | 3.3 | 0.0073 |
| false_premise | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 1.9 | 2.1 | 0.0063 |
| false_premise_casual | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.1 | 2.1 | 0.0063 |
| false_premise_keywords | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 1.6 | 1.6 | 0.0056 |
| keywords | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.7 | 2.7 | 0.0066 |
| keywords_typos | 2 | 0.75 | 1.00 | 1.00 | 0.50 | 1.00 | – | – | 2.2 | 2.6 | 0.0067 |
| loose_terms | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.1 | 2.8 | 0.0069 |
| multi_paper | 2 | 0.75 | 1.00 | 1.00 | 0.50 | 1.00 | – | – | 2.9 | 4.3 | 0.0080 |
| negative_result | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.0 | 2.0 | 0.0061 |
| non_native_grammar | 1 | 1.00 | 0.00 | 1.00 | 1.00 | 1.00 | – | – | 2.0 | 2.0 | 0.0061 |
| off_domain | 5 | – | – | – | – | – | 1.00 | – | 0.8 | 1.4 | 0.0024 |
| off_domain_casual | 1 | – | – | – | – | – | 1.00 | – | 1.6 | 1.6 | 0.0024 |
| out_of_corpus | 1 | – | – | – | – | – | 1.00 | – | 0.8 | 0.8 | 0.0022 |
| out_of_corpus_casual | 1 | – | – | – | – | – | 1.00 | – | 0.9 | 0.9 | 0.0022 |
| rambling_personal | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.9 | 3.9 | 0.0078 |
| typos | 1 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 1.7 | 1.7 | 0.0058 |

## Not correct

- q01 r1 partial: The answer correctly identifies Ythdf1's role in promoting translation of m6A-modified transcripts upon neuronal stimulation and accurately describes the impairment of synaptic transmission and LTP in Ythdf1-depleted mice, but omits the key evidence that acute hippocampal knockdown of Mettl3 (the m6A methyltransferase) also recapitulates these deficits, and does not mention that re-expressing Ythdf1 rescues the deficits.
- q02 r1 partial: The answer correctly identifies that ankyrin-2 deletion impairs remote memory while leaving recent memory intact, but misses important mechanistic details about disrupted LTP maintenance and the specific signaling pathways (BDNF/TrkB.T1/IP3R2) and reduced astrocyte-neuron contacts that explain these memory deficits.
- q04 r1 partial: The answer correctly states that presynaptic Rac1 inhibition impairs spatial working memory, but it claims postsynaptic inhibition impairs "remote memory" rather than broader "longer-term cognitive processes" as stated in the reference, which may be incomplete or potentially inconsistent with the reference's characterization of postsynaptic effects.
- q05 r1 partial: The answer correctly identifies that increased GHS-R1a impairs memory encoding, affects engram size, and blocks acquisition rather than consolidation, but it misses critical mechanistic details from the reference including suppression of neuronal excitability, blockade of memory allocation to neurons, and impaired spatial coding, and does not mention the rescue by LEAP2 antagonism or chemogenetic activation during training.
- q06 r1 wrong: The answer claims the papers don't cover this question, but the reference answer demonstrates that the papers do directly address this topic by showing the pathway is selectively needed for appetitive spatial memory (food/water location) but not for aversive spatial memory (escape location) or other forms of appetitive learning.
- q11 r1 partial: The answer correctly identifies that cofilin overactivation improves short-term memory in the object-location task and mentions benefit for spatial memory, which aligns with the reference, but omits the reference's key findings that anxiety-like behavior was unaffected and that AMPA receptor expression levels were unexpectedly unchanged.
- q12 r1 wrong: The answer claims the papers don't cover the relationship between lifting weights and memory, but the reference answer explicitly describes a study showing resistance exercise improved memory performance in rats, contradicting the student's claim.
- q14 r1 wrong: The answer claims the documents do not directly address whether mice can remember other mice from pictures, but the reference answer explicitly states they can form visuosocial memory from portrait pictures, which directly answers the question posed.
- q16 r1 partial: The answer correctly identifies key mechanisms (TrkB, PLCγ1, ankyrin-2, BDNF's role in memory persistence) and astrocyte involvement, but misses the specific roles of TrkB.T1 and IP3R2 in astrocytic signaling and fails to mention PLCγ1's specific role in CA2 visuosocial preference memory, instead focusing on CA1 LTP.
- q21 r1 wrong: The answer claims the specific results about memory deficits are not included in the document excerpts, contradicting the reference which clearly states that adult mice showed significant deficits in object recognition memory and contextual fear conditioning at 1 and 7 days post-irradiation, with hippocampal neurogenesis markers dropping within 24 hours.
- q23 r1 wrong: The answer states the papers don't address post-study pills for memory improvement, but the reference answer directly describes a PDE1 inhibitor that improved memory when given immediately after training, which is precisely a pill taken after learning that affects memory consolidation.
- q25 r1 partial: The answer correctly describes systems consolidation theory and the two-week to two-year timescale for consolidation, but it misses the key reference finding that older memories (2-year vs 12-year) show no differences in vmPFC or posterior hippocampus, and it fails to mention the important newer evidence that the hippocampus continues to actively contribute to remote memory even after lesions.
- q28 r1 partial: The answer correctly identifies that the hippocampus is involved in both memory and bodily/somatic awareness, and mentions their connection, but it does not specifically cite or reference the actual empirical evidence from the reference (the correlation between hippocampal volume and both episodic memory and somatic awareness in mild cognitive impairment patients) that directly supports this claim.
- q30 r1 partial: The answer correctly identifies the ventromedial PFC's role in controlling memory integration versus separation in the hippocampus, but misses key mechanistic details provided in the reference: the dependence on spatial context, the temporal window (7 days vs 5 hours), and the specific neural pathway through medial entorhinal cortex and neurogliaform inhibitory neurons in dorsal CA1.
- q31 r1 partial: The answer correctly identifies hippocampal mechanisms for memory separation (dentate gyrus pattern separation) but misses the reference's other key finding about neocortical GABA inhibition protecting memories from interference, and notably ends by claiming the mechanisms remain "poorly understood" despite citing evidence to the contrary.
- q33 r1 partial: The answer correctly identifies that the rostral (front) hippocampus is active during encoding and the caudal (back) hippocampus during retrieval for associative memory, but it omits the reference's additional findings about recognition memory encoding activating the rostral hippocampus selectively, and the specific electrophysiological findings about gamma power and low-frequency activity modulation.
- q35 r1 partial: The answer correctly identifies the learning and memory deficits in Ythdf1-KO mice but fails to mention the underlying molecular mechanisms (m6A reading, stimulus-dependent translation in hippocampal neurons, impaired synaptic transmission and LTP) that explain why these deficits occur.
- q36 r1 wrong: The answer incorrectly claims the papers don't contain relevant information when the reference explicitly identifies several mechanisms the corpus covers (astrocytic ankyrin-2, BDNF/TrkB.T1 signaling, hippocampal MAPK/cAMP oscillations, and CA1 place cell stability) that do address what supports memory persistence versus fading.

## Unfaithful

- q24 r1: "Working and reference memory of animals with unilateral lesions did not differ from animals with bilateral lesions and control animals."
