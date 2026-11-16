"""EV-10, EV-11: the two judges on real Claude calls. About $0.01 a run.

Run with: pytest tests/test_eval_llm.py -m llm -v
"""
import json

import pytest

from neuro_rag.config import QUESTIONS_PATH
from neuro_rag.eval.judge import judge_correctness, judge_faithfulness
from neuro_rag.generation.answer import Answer, Citation, Source, make_llm
from neuro_rag.retrieval.search import Hit


@pytest.mark.llm  # three real judge calls
def test_EV10_correctness_judge_tells_three_apart():
    # 1. q01's question and reference, from the eval set
    lines = QUESTIONS_PATH.read_text().splitlines()
    q01 = next(json.loads(line) for line in lines if line.strip() and json.loads(line)["id"] == "q01")

    # 2. three answers: complete, half of it, contradicting it; the verdict each should get
    answers = {
        "correct": "Ythdf1, which reads m6A marks, boosts translation of m6A-marked mRNAs "
                   "after neuronal stimulation in the adult hippocampus. Mice lacking Ythdf1 "
                   "learn and remember worse and have impaired synaptic transmission and LTP; "
                   "putting Ythdf1 back in the hippocampus rescues this, and knocking down "
                   "Ythdf1 or Mettl3 there causes the same deficits.",
        "partial": "Ythdf1 boosts translation of m6A-marked mRNAs after neuronal stimulation.",
        "wrong": "m6A methylation blocks translation in the hippocampus, and mice without "
                 "Ythdf1 learn faster.",
    }

    # 3. judge each one; collect every verdict first, so a failure shows all three
    llm = make_llm()
    results = {}
    for expected, text in answers.items():
        result, _, _ = judge_correctness(q01["question"], q01["reference_answer"], text, llm)
        results[expected] = result

    assert {expected: r.verdict for expected, r in results.items()} == {
        "correct": "correct", "partial": "partial", "wrong": "wrong"}
    for r in results.values():
        assert r.reason.strip()  # every verdict comes with a reason


@pytest.mark.llm  # two real judge calls
def test_EV11_faithfulness_judge_catches_unsupported_claim():
    # 1. one hit: PMC6226095 page 6, with the sentence the answers cite
    chunk = "Depletion of Ythdf1 impairs basal transmission and LTP of hippocampal synapses."
    hit = Hit(chunk_id="c1", pmcid="PMC6226095", page=6,
              title="m6A facilitates hippocampus-dependent learning and memory through Ythdf1",
              citation="Nature", license="CC BY", text=chunk, score=0.9)
    source = Source(n=1, pmcid="PMC6226095", page=6, title=hit.title, citation=hit.citation,
                    url="https://pmc.ncbi.nlm.nih.gov/articles/PMC6226095/")

    # 2. two answers citing it as [1]: one says only what the chunk says, one adds "exercise"
    def cited(text):
        return Answer(text=text, sources=[source],
                      citations=[Citation(n=1, hit_index=0, cited_text=chunk)],
                      input_tokens=0, output_tokens=0)

    supported = cited("Depleting Ythdf1 impairs basal transmission and LTP at hippocampal synapses [1].")
    unsupported = cited("Depleting Ythdf1 impairs LTP at hippocampal synapses, and exercise reverses this [1].")

    # 3. judge both
    llm = make_llm()
    good, _, _ = judge_faithfulness(supported, [hit], llm)
    bad, _, _ = judge_faithfulness(unsupported, [hit], llm)

    assert good.faithful is True
    assert good.unsupported_claim == ""
    assert bad.faithful is False
    assert "exercise" in bad.unsupported_claim.lower()
