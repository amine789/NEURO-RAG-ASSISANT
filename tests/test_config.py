import textwrap

import pytest

from neuro_rag.config import DEFAULT_CONFIG_PATH, ConfigError, load_settings

VALID_YAML = textwrap.dedent(
    """
    chunking:
      chunk_size: 512
      chunk_overlap: 64
    retrieval:
      top_k: 5
      rrf_k: 60
      embedding_model: sentence-transformers/all-MiniLM-L6-v2
      qdrant_collection: hippocampus
    models:
      grader: grader-model
      rewriter: rewriter-model
      generator: generator-model
    correction:
      relevance_threshold: 0.5
      max_rewrites: 2
      web_fallback: true
    """
)


def write(tmp_path, text):
    path = tmp_path / "config.yaml"
    path.write_text(text)
    return path


def test_valid_config_loads(tmp_path):
    s = load_settings(write(tmp_path, VALID_YAML))
    assert s.chunking.chunk_size == 512
    assert s.retrieval.qdrant_collection == "hippocampus"
    assert s.correction.web_fallback is True


def test_missing_file_raises(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_settings(tmp_path / "nope.yaml")


def test_missing_key_raises(tmp_path):
    with pytest.raises(ConfigError, match="missing keys: \\['rrf_k'\\]"):
        load_settings(write(tmp_path, VALID_YAML.replace("  rrf_k: 60\n", "")))


def test_unknown_key_raises(tmp_path):
    # A typo like "top_K" must fail loudly, not silently fall back to nothing.
    with pytest.raises(ConfigError, match="unknown keys"):
        load_settings(write(tmp_path, VALID_YAML.replace("top_k:", "top_K:")))


def test_empty_env_var_treated_as_unset(tmp_path, monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "")
    assert load_settings(write(tmp_path, VALID_YAML)).qdrant_url is None


def test_project_config_yaml_is_valid():
    # Fails until you write config.yaml at the project root.
    load_settings(DEFAULT_CONFIG_PATH)
