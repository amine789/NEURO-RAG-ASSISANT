# Observability: validation

How each acceptance criterion in [spec.md](spec.md) is checked, and the results.
The examples are in the spec; this file says where each one runs.

## Checks

- **Unit test:** the API with a recording tracer (a fake that keeps traces in a
  list) and a fake pipeline; nothing is sent anywhere.
- **Service test:** the real service; Langfuse pointed at a closed port (OB-5)
  or left without keys (OB-6).
- **Manual:** a person opens the trace in Langfuse Cloud (OB-8).

| Criterion | Kind | Test |
|---|---|---|
| OB-1 | unit | `test_OB1_one_trace_with_three_steps_in_order` |
| OB-2 | unit | `test_OB2_retrieve_and_rerank_show_chosen_chunks` |
| OB-3 | unit | `test_OB3_generate_records_model_tokens_and_cost` |
| OB-4 | unit | `test_OB4_failed_request_is_traced_with_its_error` |
| OB-5 | service | `test_OB5_langfuse_unreachable_does_not_break_answers` |
| OB-6 | unit | `test_OB6_no_keys_means_tracing_off` |
| OB-7 | unit | `test_OB7_no_api_key_in_traces` |
| OB-8 | manual | send one question, open its `trace_id` in Langfuse Cloud, check the list in the spec |

## Results

| Date | Version | Result | Notes |
|---|---|---|---|
| 2026-10-20 | Langfuse Cloud (EU), SDK 4.17 | all 8 criteria pass | OB-8 checked by hand: trace "ask" with steps retrieve, rerank and generate, their durations, model, tokens and cost shown in Langfuse |
