import os

# Tests send nothing to Langfuse unless a run asks for it:
#   LANGFUSE_TRACING_ENABLED=true pytest tests/test_tracing_live.py -m langfuse
# setdefault keeps a value set on the command line; load_dotenv() never overrides it.
os.environ.setdefault("LANGFUSE_TRACING_ENABLED", "false")
