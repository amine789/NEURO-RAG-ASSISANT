"""Judge tests for specs/eval/spec.md with the real judge model (EV-8, EV-9). They cost money.

    pytest tests/test_eval_llm.py -m llm -v
"""
import os

import pytest

from neuro_rag.eval.judge import Judge

pytestmark = [pytest.mark.llm,
              pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="no ANTHROPIC_API_KEY")]

QUESTION = "How does m6A RNA methylation support hippocampus-dependent learning and memory?"
REFERENCE = ("The m6A reader Ythdf1 enhances translation of m6A-modified transcripts in a neuronal-stimulus-dependent "
             "way in the adult mouse hippocampus. Ythdf1-knockout mice show learning and memory defects plus impaired "
             "hippocampal synaptic transmission and LTP; re-expressing Ythdf1 in the hippocampus rescues these, and "
             "acute hippocampal knockdown of Ythdf1 or Mettl3 (the m6A methyltransferase) recapitulates the deficits.")
CHUNK = "Ythdf1 knockout mice show learning defects."


@pytest.fixture(scope="module")
def judge():
    return Judge()


def test_EV8_partial_answer_is_judged_partial(judge):
    answer = "The m6A reader Ythdf1 enhances translation of m6A-modified transcripts in the hippocampus. [1]"

    verdict = judge.correctness(QUESTION, REFERENCE, answer)

    print(f"\n{verdict}")
    assert verdict.verdict == "partial"


def test_EV8_complete_answer_is_judged_correct(judge):
    verdict = judge.correctness(QUESTION, REFERENCE, REFERENCE)
    assert verdict.verdict == "correct"


def test_EV9_supported_answer_is_faithful(judge):
    result = judge.faithfulness("Ythdf1 knockout mice show learning defects [1].", {1: [CHUNK]})
    assert result.faithful is True


def test_EV9_unsupported_claim_is_judged_unfaithful(judge):
    answer = "Ythdf1 knockout mice show learning defects, and the effect is reversed by exercise [1]."

    result = judge.faithfulness(answer, {1: [CHUNK]})

    print(f"\n{result}")
    assert result.faithful is False
    assert "exercise" in result.unsupported_claim
