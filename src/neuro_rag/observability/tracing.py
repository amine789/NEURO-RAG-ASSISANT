"""One trace per request, with a timed step per pipeline stage.

Spec: docs/specs/observability/spec.md (OB-1 to OB-8).

The rest of the code only sees `Tracer`, `Trace` and `Step`. Everything passed
to them is redacted before it reaches a backend, so no backend can leak an API
key (OB-7). The backend is Langfuse when its keys are set, and nothing at all
otherwise (OB-6); tests record into a list instead.
"""
import logging
import os
import uuid
from contextlib import contextmanager
from typing import Any, Iterator

log = logging.getLogger(__name__)

# Environment variables whose values must never leave the server (ROADMAP: Security).
SECRET_ENV = ("ANTHROPIC_API_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_PUBLIC_KEY", "QDRANT_API_KEY",
              "FIRECRAWL_API_KEY")
REDACTED = "[redacted]"


def redact(value: Any) -> Any:
    """`value` with every secret from the environment replaced, in strings at any depth."""
    secrets = [s for s in (os.getenv(name) for name in SECRET_ENV) if s]
    return _redact(value, secrets) if secrets else value


def _redact(value: Any, secrets: list[str]) -> Any:
    if isinstance(value, str):
        for s in secrets:
            value = value.replace(s, REDACTED)
        return value
    if isinstance(value, dict):
        return {k: _redact(v, secrets) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact(v, secrets) for v in value]
    return value


def _error_message(e: BaseException) -> str:
    return redact(f"{type(e).__name__}: {e}")


class Step:
    """One timed stage of a request; ends when its `with` block does."""

    def __init__(self, tracer: "Tracer", handle):
        self._tracer, self._handle = tracer, handle

    def update(self, **fields) -> None:
        """input, output, model, usage ({"input": n, "output": n}) or cost (dollars)."""
        self._tracer._update(self._handle, **redact(fields))


class Trace(Step):
    """A whole request. `id` is returned to the client so a report can be matched to it (OB-1)."""

    @property
    def id(self) -> str:
        return self._tracer._trace_id(self._handle)

    @contextmanager
    def step(self, name: str, kind: str = "span", **fields) -> Iterator[Step]:
        """kind is "span", or "generation" for an LLM call (it carries model, tokens and cost)."""
        handle = self._tracer._start_step(self._handle, name, kind, **redact(fields))
        try:
            yield Step(self._tracer, handle)
        except Exception as e:
            self._tracer._update(handle, error=_error_message(e))  # the failed step shows why (OB-4)
            raise
        finally:
            self._tracer._end(handle)


class Tracer:
    """No backend: traces go nowhere but still get an ID (OB-6). Backends override the hooks."""

    @contextmanager
    def trace(self, name: str, input: Any) -> Iterator[Trace]:
        handle = self._start_trace(name, input=redact(input))
        trace = Trace(self, handle)
        try:
            yield trace
        except Exception as e:
            self._update(handle, error=_error_message(e))
            raise
        finally:
            self._end(handle)

    def flush(self) -> None:
        """Send what is buffered; called when the service stops."""

    # Backend hooks. A handle is whatever the backend needs to find a trace or step again.

    def _start_trace(self, name: str, **fields):
        return uuid.uuid4().hex

    def _start_step(self, parent, name: str, kind: str, **fields):
        return parent

    def _update(self, handle, **fields) -> None:
        pass

    def _end(self, handle) -> None:
        pass

    def _trace_id(self, handle) -> str:
        return handle


class LangfuseTracer(Tracer):
    """Sends to Langfuse Cloud. The SDK exports in a background thread, so a slow or unreachable
    Langfuse never delays an answer (OB-5); failures are logged by the SDK as warnings."""

    def __init__(self, client=None):
        from langfuse import Langfuse

        self.client = client or Langfuse()

    def _start_trace(self, name, **fields):
        return self.client.start_observation(name=name, as_type="span", **fields)

    def _start_step(self, parent, name, kind, **fields):
        return parent.start_observation(name=name, as_type=kind, **_langfuse_fields(fields))

    def _update(self, handle, **fields):
        handle.update(**_langfuse_fields(fields))

    def _end(self, handle):
        handle.end()

    def _trace_id(self, handle):
        return handle.trace_id

    def flush(self):
        self.client.flush()


def _langfuse_fields(fields: dict) -> dict:
    """Our field names -> the Langfuse SDK's."""
    out = dict(fields)
    if "usage" in out:
        out["usage_details"] = out.pop("usage")
    if "cost" in out:
        out["cost_details"] = {"total": out.pop("cost")}
    if "error" in out:
        out["level"], out["status_message"] = "ERROR", out.pop("error")
    return out


def make_tracer() -> Tracer:
    """Langfuse if both keys are set; otherwise tracing is off, said once at startup (OB-6)."""
    if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
        log.info("tracing on: Langfuse at %s",
                 os.getenv("LANGFUSE_BASE_URL") or os.getenv("LANGFUSE_HOST") or "https://cloud.langfuse.com")
        return LangfuseTracer()
    log.warning("tracing is off: LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are not both set")
    return Tracer()
