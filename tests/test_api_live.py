import re

import pytest
from fastapi.testclient import TestClient

from neuro_rag.api.app import create_app

Q01 = "How does m6A RNA methylation support hippocampus-dependent learning and memory?"


@pytest.mark.integration  # needs Qdrant running
@pytest.mark.llm  # one real Claude call, about $0.003
def test_AP7_real_app_answers_q01():
    client = TestClient(create_app())  # no fakes: build_pipeline() builds the real ones

    response = client.post("/ask", json={"question": Q01})

    assert response.status_code == 200
    body = response.json()
    assert len(body["sources"]) >= 1
    markers = {int(n) for n in re.findall(r"\[(\d+)\]", body["answer"])}
    assert markers <= {s["n"] for s in body["sources"]}  # every [n] has a source
    for s in body["sources"]:
        assert s["url"].startswith("https://pmc.ncbi.nlm.nih.gov/articles/PMC")
