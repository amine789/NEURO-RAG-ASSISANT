# Eval report: crag_x3

150 runs, 0 failed, 0 judge calls failed, $0.83 total

| questions | runs | correctness | faithful | paper@5 | page@5 | cites expected | not covered | cites papers | p50 s | p95 s | $ per run |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 150 | 0.79 | 0.97 | 0.91 | 0.74 | 0.90 | 0.75 | 0.89 | 4.1 | 22.8 | 0.0055 |
| borderline | 18 | – | 0.88 | – | – | – | – | 0.89 | 16.9 | 24.1 | 0.0046 |
| broad_vague | 3 | 0.00 | – | 0.00 | 0.00 | 0.00 | – | – | 3.6 | 3.8 | 0.0042 |
| casual | 9 | 0.56 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.7 | 4.6 | 0.0064 |
| casual_loose_terms | 12 | 0.83 | 1.00 | 0.75 | 0.75 | 0.75 | – | – | 4.5 | 6.3 | 0.0065 |
| casual_multi_paper | 3 | 0.50 | 1.00 | 1.00 | 0.00 | 1.00 | – | – | 4.5 | 5.1 | 0.0077 |
| casual_typos | 3 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.5 | 4.0 | 0.0067 |
| clinical_loose | 3 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 4.3 | 5.0 | 0.0071 |
| direct | 21 | 0.86 | 1.00 | 0.86 | 0.57 | 0.86 | – | – | 3.5 | 21.8 | 0.0063 |
| direct_computational | 3 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.4 | 3.6 | 0.0067 |
| direct_human | 6 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 4.1 | 4.5 | 0.0069 |
| false_premise | 6 | 0.83 | 1.00 | 0.83 | 0.33 | 0.67 | – | – | 13.2 | 21.4 | 0.0056 |
| false_premise_casual | 3 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.5 | 3.7 | 0.0064 |
| false_premise_keywords | 3 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 23.6 | 25.9 | 0.0061 |
| keywords | 3 | 0.67 | 1.00 | 1.00 | 0.00 | 1.00 | – | – | 4.5 | 5.0 | 0.0070 |
| keywords_typos | 6 | 0.83 | 1.00 | 1.00 | 0.50 | 1.00 | – | – | 5.0 | 5.3 | 0.0077 |
| loose_terms | 6 | 0.92 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.6 | 4.5 | 0.0066 |
| multi_paper | 6 | 0.58 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 4.9 | 5.6 | 0.0081 |
| negative_result | 3 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.8 | 3.9 | 0.0069 |
| non_native_grammar | 3 | 1.00 | 0.33 | 1.00 | 1.00 | 1.00 | – | – | 3.4 | 3.8 | 0.0062 |
| off_domain | 15 | – | – | – | – | – | 1.00 | – | 0.3 | 0.3 | 0.0000 |
| off_domain_casual | 3 | – | – | – | – | – | 1.00 | – | 0.3 | 0.3 | 0.0000 |
| out_of_corpus | 3 | – | 1.00 | – | – | – | 0.00 | – | 15.6 | 19.8 | 0.0053 |
| out_of_corpus_casual | 3 | – | 1.00 | – | – | – | 0.00 | – | 27.4 | 33.6 | 0.0059 |
| rambling_personal | 3 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 5.2 | 5.2 | 0.0076 |
| typos | 3 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.0 | 3.7 | 0.0058 |

## Not correct

- q02 r1 partial: The answer correctly identifies that ankyrin-2 deletion impairs remote memory while leaving recent memory intact, and correctly mentions disruption of LTP maintenance, but omits the important mechanisms involving reduced astrocyte contacts with engram neurons and impaired astrocyte morphogenesis through BDNF/TrkB.T1/IP3R2 signaling.
- q02 r3 partial: The answer correctly identifies that ankyrin-2 deletion impairs remote memory while leaving recent memory intact and disrupts LTP maintenance, but it omits the mechanistic details about reduced astrocyte contacts with engram neurons and impaired astrocyte morphogenesis through BDNF/TrkB.T1/IP3R2 signaling.
- q05 r1 partial: The answer correctly identifies the main finding that GHS-R1a elevation impairs memory formation and accurately describes the mechanistic details about suppressed excitability, blocked memory allocation, impaired spatial coding, and reduced engram size, but omits important contextual information about LEAP2 and the rescue experiment via chemogenetic activation that demonstrate functional significance.
- q06 r1 partial: The answer correctly identifies that the ventral hippocampus to lateral septum pathway selectively supports appetitive (rewarding) spatial memory and does not affect escape location memory under negative reinforcement, but it fails to mention that the pathway also does not affect food intake or social/olfactory appetitive learning, which are important specifics about the selectivity of this pathway.
- q06 r2 partial: The answer correctly identifies that the ventral hippocampus-lateral septum pathway is not needed for all spatial memory types and specifically notes impairment of appetitive spatial memory while sparing escape location memory, but it misses the reference's key finding that the pathway selectively supports foraging-related (food/water location) memory and doesn't mention that non-spatial appetitive learning (food intake, social/olfactory learning) is also unaffected.
- q06 r3 partial: The answer correctly identifies that the ventral hippocampus-to-lateral septum pathway does not support all spatial memory types and accurately notes that it doesn't affect escape location memory, but it fails to mention that the pathway specifically supports appetitive/foraging-related memory while sparing food intake and social/olfactory learning.
- q12 r1 partial: The answer correctly identifies the rat model findings and the IGF-1 mechanism from the reference, but introduces human study results that are not mentioned in the reference answer, which explicitly states "The evidence in the corpus is from an animal model."
- q12 r2 wrong: The answer contradicts the reference by claiming evidence from human studies, when the reference explicitly states "The evidence in the corpus is from an animal model" and specifies only rat studies.
- q12 r3 partial: The answer correctly states the rat study findings about resistance exercise improving hippocampus-dependent memory with increased IGF-1/IGF-1R, but the reference explicitly notes "the evidence in the corpus is from an animal model," whereas the answer claims human studies in the corpus demonstrated these effects, which is not supported by the reference answer.
- q13 r1 partial: The answer correctly identifies the study population (rats), the diet type (cafeteria-style/Western diet), the developmental period (juvenile and adolescent), the specific memory impairment (hippocampus-dependent contextual episodic memory), and the persistence of deficits despite dietary intervention, but omits the mechanistic finding about dysregulated acetylcholine signaling in the dorsal hippocampus.
- q13 r2 partial: The answer correctly identifies the key findings about hippocampus-dependent contextual episodic memory impairments in rats from juvenile/adolescent cafeteria-diet consumption and their persistence into adulthood despite dietary intervention, but omits the reference answer's crucial mechanistic finding about dysregulated acetylcholine signaling in the dorsal hippocampus.
- q14 r2 partial: The answer correctly establishes that mice can form visuosocial memories and learned associations with mouse photos, but it misses the reference's key finding that mice can distinguish conspecifics from other species through visuosocial memory formation and fails to mention the specific neural mechanism involving PLCγ1 in hippocampal CA2.
- q14 r3 partial: The answer correctly establishes that mice have visuosocial memory and can remember other mice from pictures, but it focuses primarily on fear-conditioned associations with photos rather than the reference's main finding about simple visual discrimination and conspecific recognition, and it fails to mention the critical molecular mechanism (PLCγ1 in hippocampal CA2) that the reference emphasizes.
- q15 r2 partial: The answer correctly identifies that MAPK and cAMP signaling oscillates with circadian rhythm and that interfering with these oscillations impairs memory persistence, but it fails to mention the critical finding about Bmal1 knockout mice having impaired contextual fear and spatial memory, reduced Schaffer-collateral LTP, and loss of training-induced Erk1/2 MAPK activation.
- q15 r3 partial: The answer correctly describes hippocampal MAPK and cAMP oscillations, their role in memory consolidation, interference effects, and Bmal1-deficient mice having impaired contextual fear, spatial memory, and reduced LTP; however, it fails to mention the critical finding that Bmal1-deficient mice lose both training-induced Erk1/2 MAPK activation and the diurnal oscillation of MAPK and cAMP in the hippocampus itself.
- q16 r1 partial: The answer correctly identifies astrocytic TrkB.T1 signaling, ankyrin-2 (Ank2), and remote memory enhancement, as well as PLCγ1's role in BDNF signaling, but it does not specify that PLCγ1 is required for CA2 neuron-specific visuosocial preference memory, which is a key finding in the reference answer.
- q16 r2 partial: The answer correctly captures the key roles of BDNF signaling in astrocytes supporting memory persistence through TrkB.T1, ankyrin-2, and optogenetic enhancement of remote memory, and correctly identifies PLCγ1 as a downstream signaling molecule, but fails to specify that PLCγ1 is required for visuosocial preference memory in CA2 neurons, which is a main finding in the reference answer.
- q16 r3 partial: The answer correctly identifies astrocytic TrkB.T1 signaling enhancing remote memory and PLCγ1 as a downstream BDNF pathway molecule, but it fails to mention the specific morphogenesis-dependent mechanism in astrocytes (ankyrin-2, IP3R2, morphological changes) or the specific role of PLCγ1 in CA2 neurons for visuosocial preference memory, thereby missing key mechanistic details from the reference.
- q18 r1 wrong: The answer incorrectly accepts the false premise of the question by suggesting the hippocampus is needed for procedural memory replay during sleep, whereas the reference answer correctly identifies that this premise is wrong—procedural memory replay occurs independently of the hippocampus in the dorsal striatum and persists after hippocampal lesions.
- q21 r1 partial: The answer correctly identifies object recognition memory deficits at 1 and 7 days post-irradiation and mentions reduced hippocampal neurogenesis as a mechanism, but it misses the reference's finding about contextual fear conditioning deficits and incorrectly characterizes the effects as temporary/transient rather than demonstrating the persistent deficits shown at 7 days.
- q21 r2 partial: The answer correctly describes memory deficits in object recognition and their timeline, reduced hippocampal neurogenesis markers, and the mechanistic link between neurogenesis inhibition and memory loss, but omits the reference's key finding that contextual fear conditioning was also significantly impaired by the neutron irradiation.
- q21 r3 partial: The answer correctly describes memory deficits in object recognition, the timing of testing (1 and 7 days post-irradiation), the involvement of reduced neurogenesis markers (Ki-67, DCX), and the 24-hour timeframe for marker reduction, but introduces the claim that effects are "temporary rather than permanent" which is not established in the reference answer and contradicts the typical understanding of such irradiation damage.
- q22 r2 partial: The answer correctly states that PDE1B knockdown enhances both contextual and spatial memory in the hippocampus, but it misses the reference's key point that PDE1B knockdown does not affect non-cognitive behavior and omits the explicit statement that PDE1B acts as a negative regulator of memory.
- q22 r3 partial: The answer correctly states that PDE1B knockdown enhances contextual and spatial memory, but it fails to address whether non-cognitive behavior was affected, which is a key part of the reference answer's claim that knockdown did not affect non-cognitive behavior.
- q25 r1 partial: The answer correctly captures the nuanced view that memories don't simply "move out" and mentions the shift toward vmPFC involvement and continued hippocampal contributions, but it omits the key reference finding that the hippocampus still actively contributes to remote memories (contradicting the classic systems-consolidation view).
- q25 r2 partial: The answer correctly describes key findings about vmPFC involvement and hippocampal representation of older memories, but omits the critical reference point that newer rodent evidence shows the hippocampus still actively contributes to remote memory, contradicting the classic systems-consolidation view that the reference emphasizes as an important caveat.
- q25 r3 partial: The answer correctly describes the vmPFC findings and the changing neural patterns in the hippocampus, but omits the key reference finding that newer rodent evidence shows the hippocampus still actively contributes to remote memory and contradicts the classical systems-consolidation view that memories simply move to neocortex.
- q26 r2 partial: The answer correctly captures that both the number of stable place cells and their stability increase across learning, but it misses the key point that stable cells over-represented task-relevant information and correlated with performance, and it frames the daily BTSP mechanism somewhat differently by emphasizing "daily reconstitution" rather than the reference's framing of increasing likelihood of neuron-specific plasticity per day rather than long-term stabilization of synaptic weights.
- q30 r1 partial: The answer correctly identifies that the vmPFC controls whether memories are integrated or separated in the hippocampus, but misses critical details from the reference including the temporal spacing requirement (7 days vs 5 hours), the dependence on shared spatial context, and the specific neural mechanisms involving projections to medial entorhinal cortex and neurogliaform inhibitory neurons in dorsal CA1.
- q30 r2 partial: The answer correctly identifies that the vmPFC controls memory integration versus separation in the hippocampus, but fails to describe key mechanistic details provided in the reference: the dependence on spatial context similarity, the temporal distance requirement (7 days vs 5 hours), the role of direct projections to medial entorhinal cortex, and the involvement of neurogliaform inhibitory neurons in dorsal CA1.
- q30 r3 partial: The answer correctly identifies that the ventromedial prefrontal cortex controls whether memories are integrated or separated in the hippocampus, but misses key details from the reference about the role of spatial context, the 7-day temporal window, the direct projections to medial entorhinal cortex, and the involvement of neurogliaform inhibitory neurons in CA1.
- q31 r1 partial: The answer correctly identifies hippocampal mechanisms (specifically the dentate gyrus) for separating overlapping memories using contextual/relational information, which aligns with the reference answer, but completely omits the neocortical GABAergic inhibition mechanism and the brain stimulation evidence that are key components of the reference's findings.
- q31 r2 partial: The answer correctly describes the hippocampal mechanism for memory separation using relational/contextual information (dentate gyrus pattern separation), but it notably omits the neocortical GABAergic inhibition mechanism mentioned in the reference answer as a key mechanism preventing memory interference.
- q31 r3 partial: The answer correctly identifies hippocampal mechanisms for separating overlapping memories and uses relational/contextual information, but it completely omits the neocortical GABAergic inhibition mechanism that is a key component of the reference answer, thus missing approximately half of the reference's main findings.
- q33 r1 partial: The answer correctly identifies that the rostral hippocampus is active during encoding and the caudal hippocampus during retrieval for associative memory, but misses additional findings about recognition memory encoding and the role of congruence in modulating low-frequency activity in the caudal hippocampus.
- q35 r3 wrong: The answer claims the papers don't explain the underlying biological reason, but the reference answer clearly states that Ythdf1 reads m6A marks and promotes stimulus-dependent translation of target mRNAs in hippocampal neurons—this is the mechanistic explanation for the learning deficits that the answer says is absent from the papers.
- q36 r1 wrong: The answer incorrectly claims the corpus doesn't cover the topic, when the reference explicitly identifies multiple mechanisms in the provided papers: astrocytic ankyrin-2 and BDNF/TrkB.T1 signaling, circadian oscillations of hippocampal MAPK/cAMP signaling, and CA1 place cell stability changes.
- q36 r2 wrong: The answer incorrectly claims the papers don't address the question, when the reference answer identifies multiple mechanisms in the corpus (astrocytic ankyrin-2, BDNF/TrkB.T1 signaling, circadian oscillations of MAPK/cAMP signaling, and CA1 place cell stability) that do directly address factors determining memory persistence and fade.
- q36 r3 wrong: The answer claims the papers don't cover memory persistence mechanisms, but the reference indicates the corpus does address this through multiple specific mechanisms (astrocytic ankyrin-2, BDNF/TrkB.T1 signaling, circadian oscillations of hippocampal MAPK/cAMP signaling, and CA1 place cell stability), so the answer is factually incorrect about the papers' coverage.

## Unfaithful

- q24 r1: "Working and reference memory of animals with unilateral lesions did not differ from animals with bilateral lesions and control animals."
- q24 r2: "working and reference memory of animals with unilateral lesions did not differ from animals with bilateral lesions and control animals [2]"
- q45 r1: "caffeine administered after learning can enhance object recognition memory consolidation by improving discrimination between previously seen targets and similar lures"
- q45 r2: "caffeine effects appear detrimental to short-term and working memory, whereas the effects are somewhat positive for long-term memory"

## Loop

| kind | runs | declined | rewrites (mean) | web used | not covered |
|---|---|---|---|---|---|
| answer_from_corpus | 96 | 0 | 0.11 | 3 | 0 |
| correct_premise | 12 | 0 | 1.50 | 1 | 0 |
| decline | 18 | 18 | 0.00 | 0 | 0 |
| not_declined | 18 | 0 | 1.67 | 15 | 0 |
| web_fallback | 6 | 0 | 2.00 | 6 | 0 |

Paths:

- q01 answer_from_corpus: retrieve → grade:good → generate
- q01 answer_from_corpus: retrieve → grade:good → generate
- q01 answer_from_corpus: retrieve → grade:good → generate
- q02 answer_from_corpus: retrieve → grade:good → generate
- q02 answer_from_corpus: retrieve → grade:good → generate
- q02 answer_from_corpus: retrieve → grade:good → generate
- q03 answer_from_corpus: retrieve → grade:good → generate
- q03 answer_from_corpus: retrieve → grade:good → generate
- q03 answer_from_corpus: retrieve → grade:good → generate
- q04 answer_from_corpus: retrieve → grade:good → generate
- q04 answer_from_corpus: retrieve → grade:good → generate
- q04 answer_from_corpus: retrieve → grade:good → generate
- q05 answer_from_corpus: retrieve → grade:good → generate
- q05 answer_from_corpus: retrieve → grade:good → generate
- q05 answer_from_corpus: retrieve → grade:good → generate
- q06 answer_from_corpus: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q06 answer_from_corpus: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q06 answer_from_corpus: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q07 answer_from_corpus: retrieve → grade:good → generate
- q07 answer_from_corpus: retrieve → grade:good → generate
- q07 answer_from_corpus: retrieve → grade:good → generate
- q08 answer_from_corpus: retrieve → grade:good → generate
- q08 answer_from_corpus: retrieve → grade:good → generate
- q08 answer_from_corpus: retrieve → grade:good → generate
- q09 answer_from_corpus: retrieve → grade:good → generate
- q09 answer_from_corpus: retrieve → grade:good → generate
- q09 answer_from_corpus: retrieve → grade:good → generate
- q10 answer_from_corpus: retrieve → grade:good → generate
- q10 answer_from_corpus: retrieve → grade:good → generate
- q10 answer_from_corpus: retrieve → grade:good → generate
- q11 answer_from_corpus: retrieve → grade:good → generate
- q11 answer_from_corpus: retrieve → grade:good → generate
- q11 answer_from_corpus: retrieve → grade:good → generate
- q12 answer_from_corpus: retrieve → grade:good → generate
- q12 answer_from_corpus: retrieve → grade:good → generate
- q12 answer_from_corpus: retrieve → grade:good → generate
- q13 answer_from_corpus: retrieve → grade:good → generate
- q13 answer_from_corpus: retrieve → grade:good → generate
- q13 answer_from_corpus: retrieve → grade:good → generate
- q14 answer_from_corpus: retrieve → grade:good → generate
- q14 answer_from_corpus: retrieve → grade:good → generate
- q14 answer_from_corpus: retrieve → grade:good → generate
- q15 answer_from_corpus: retrieve → grade:good → generate
- q15 answer_from_corpus: retrieve → grade:good → generate
- q15 answer_from_corpus: retrieve → grade:good → generate
- q16 answer_from_corpus: retrieve → grade:good → generate
- q16 answer_from_corpus: retrieve → grade:good → generate
- q16 answer_from_corpus: retrieve → grade:good → generate
- q17 correct_premise: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:weak → fallback → generate
- q17 correct_premise: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:weak → fallback → generate
- q17 correct_premise: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:weak → fallback → generate
- q18 correct_premise: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q18 correct_premise: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:good → generate
- q18 correct_premise: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:good → generate
- q19 web_fallback: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q19 web_fallback: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q19 web_fallback: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q20 decline: declined
- q20 decline: declined
- q20 decline: declined
- q21 answer_from_corpus: retrieve → grade:good → generate
- q21 answer_from_corpus: retrieve → grade:good → generate
- q21 answer_from_corpus: retrieve → grade:good → generate
- q22 answer_from_corpus: retrieve → grade:good → generate
- q22 answer_from_corpus: retrieve → grade:good → generate
- q22 answer_from_corpus: retrieve → grade:good → generate
- q23 answer_from_corpus: retrieve → grade:good → generate
- q23 answer_from_corpus: retrieve → grade:good → generate
- q23 answer_from_corpus: retrieve → grade:good → generate
- q24 answer_from_corpus: retrieve → grade:good → generate
- q24 answer_from_corpus: retrieve → grade:good → generate
- q24 answer_from_corpus: retrieve → grade:good → generate
- q25 answer_from_corpus: retrieve → grade:good → generate
- q25 answer_from_corpus: retrieve → grade:good → generate
- q25 answer_from_corpus: retrieve → grade:good → generate
- q26 answer_from_corpus: retrieve → grade:good → generate
- q26 answer_from_corpus: retrieve → grade:good → generate
- q26 answer_from_corpus: retrieve → grade:good → generate
- q27 answer_from_corpus: retrieve → grade:good → generate
- q27 answer_from_corpus: retrieve → grade:good → generate
- q27 answer_from_corpus: retrieve → grade:good → generate
- q28 answer_from_corpus: retrieve → grade:good → generate
- q28 answer_from_corpus: retrieve → grade:good → generate
- q28 answer_from_corpus: retrieve → grade:good → generate
- q29 answer_from_corpus: retrieve → grade:good → generate
- q29 answer_from_corpus: retrieve → grade:good → generate
- q29 answer_from_corpus: retrieve → grade:good → generate
- q30 answer_from_corpus: retrieve → grade:good → generate
- q30 answer_from_corpus: retrieve → grade:good → generate
- q30 answer_from_corpus: retrieve → grade:good → generate
- q31 answer_from_corpus: retrieve → grade:good → generate
- q31 answer_from_corpus: retrieve → grade:good → generate
- q31 answer_from_corpus: retrieve → grade:good → generate
- q32 answer_from_corpus: retrieve → grade:good → generate
- q32 answer_from_corpus: retrieve → grade:good → generate
- q32 answer_from_corpus: retrieve → grade:good → generate
- q33 answer_from_corpus: retrieve → grade:weak → rewrite → retrieve → grade:good → generate
- q33 answer_from_corpus: retrieve → grade:weak → rewrite → retrieve → grade:good → generate
- q33 answer_from_corpus: retrieve → grade:weak → rewrite → retrieve → grade:good → generate
- q34 answer_from_corpus: retrieve → grade:good → generate
- q34 answer_from_corpus: retrieve → grade:good → generate
- q34 answer_from_corpus: retrieve → grade:good → generate
- q35 answer_from_corpus: retrieve → grade:good → generate
- q35 answer_from_corpus: retrieve → grade:good → generate
- q35 answer_from_corpus: retrieve → grade:good → generate
- q36 answer_from_corpus: retrieve → grade:weak → rewrite → retrieve → grade:good → generate
- q36 answer_from_corpus: retrieve → grade:good → generate
- q36 answer_from_corpus: retrieve → grade:weak → rewrite → retrieve → grade:good → generate
- q41 correct_premise: retrieve → grade:good → generate
- q41 correct_premise: retrieve → grade:good → generate
- q41 correct_premise: retrieve → grade:good → generate
- q42 correct_premise: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:weak → fallback → generate
- q42 correct_premise: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:weak → fallback → generate
- q42 correct_premise: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:good → generate
- q43 web_fallback: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q43 web_fallback: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q43 web_fallback: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q44 decline: declined
- q44 decline: declined
- q44 decline: declined
- q45 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q45 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q45 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q46 not_declined: retrieve → grade:good → generate
- q46 not_declined: retrieve → grade:good → generate
- q46 not_declined: retrieve → grade:good → generate
- q47 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q47 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q47 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q48 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q48 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q48 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q49 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q49 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q49 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q50 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q50 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q50 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
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
