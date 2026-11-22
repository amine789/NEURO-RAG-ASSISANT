"""Guard for CR-11's leak (2026-11-22): no traced step may record an object holding keys.

Langfuse's @observe records a function's arguments as the span's input. rewrite() took
the LLM object as an argument, so its Langfuse callback, secret key included, was
serialized into the trace. This test reads the source of every module with @observe
steps and fails if a traced function takes an argument that holds clients or keys
(llm, client, rerank, count, embed) without capture_input=False.

No network, no Langfuse: it only parses the code.
Run: pytest tests/test_trace_secrets.py -v
"""
import ast
from pathlib import Path

import pytest

SRC = Path(__file__).parents[1] / "src" / "neuro_rag"
TRACED_MODULES = [SRC / "crag" / "loop.py", SRC / "api" / "app.py"]
OBJECT_ARGS = {"llm", "client", "rerank", "count", "embed", "sparse_embed"}


def traced_functions(path):
    """(name, args, capture_input) for every function decorated with @observe(...) in the file."""
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if not isinstance(node, ast.FunctionDef):
            continue
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and getattr(dec.func, "id", None) == "observe":
                capture = next((k.value.value for k in dec.keywords if k.arg == "capture_input"), True)
                yield node.name, {a.arg for a in node.args.args}, capture


@pytest.mark.parametrize("path", TRACED_MODULES, ids=lambda p: p.name)
def test_traced_steps_never_record_objects_with_keys(path):
    leaks = [name for name, args, capture in traced_functions(path) if capture and args & OBJECT_ARGS]
    assert leaks == [], f"traced with object arguments recorded: {leaks}; add capture_input=False"


def test_the_guard_sees_the_steps():
    names = {name for p in TRACED_MODULES for name, _, _ in traced_functions(p)}
    assert {"grade", "rewrite", "web_hits", "run_loop"} <= names
