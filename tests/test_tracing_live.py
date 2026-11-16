"""TR-6: Langfuse's cost for a real Claude call equals ours. About $0.003 a run.

Run with: LANGFUSE_TRACING_ENABLED=true pytest tests/test_tracing_live.py -m langfuse -v
"""
import os
import time
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from langfuse import get_client

from neuro_rag.api.app import create_app
from neuro_rag.eval.run import cost

Q01 = "How does m6A RNA methylation support hippocampus-dependent learning and memory?"


@pytest.mark.integration  # needs Qdrant running
@pytest.mark.llm  # one real Claude call, about $0.003
@pytest.mark.langfuse  # sends a trace to Langfuse and reads it back
@pytest.mark.skipif(os.environ.get("LANGFUSE_TRACING_ENABLED") != "true",
                    reason="tracing is off; run with LANGFUSE_TRACING_ENABLED=true")
def test_TR6_langfuse_cost_equals_ours():
    # 1. one real request, with t0 just before it so we only read this run's generation
    t0 = datetime.now(timezone.utc)
    response = TestClient(create_app()).post("/ask", json={"question": Q01})
    assert response.status_code == 200

    # 2. send the buffered traces now instead of waiting for the background thread
    langfuse = get_client()
    langfuse.flush()

    # 3. Langfuse computes cost after ingesting: read every 5 s, for up to 60 s
    generation = None
    for _ in range(12):
        found = langfuse.api.observations.get_many(
            type="GENERATION", from_start_time=t0, fields="core,basic,usage").data
        priced = [g for g in found if g.total_cost]
        if priced:
            generation = priced[0]
            break
        time.sleep(5)
    assert generation is not None, "no generation with a cost in Langfuse after 60 s"

    # 4. their cost equals our formula on the same token counts
    usage = generation.usage_details
    assert round(generation.total_cost, 6) == round(cost(usage["input"], usage["output"]), 6)
