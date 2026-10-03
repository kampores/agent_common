# 7.5. Inference Results and Error Handling

[All LLM manuals](01_unified_llm_client_en.md)

> Start with [7.1 Model Profiles and Text Generation](01_model_profiles_and_generation_en.md) for configuration and the minimal call.

## 1. Failure handling

Missing profiles, unsupported providers, HTTP/URL errors, required response-field errors, and missing local inference dependencies can raise `LlmInferenceError`. Disabled external calls, missing API keys, and missing local model files can produce `None` instead.

JSON decoding, numeric conversion, some timeout errors, and model loading/execution failures can propagate their original exception types. Do not assume every failure becomes `LlmInferenceError`. Handle expected exceptions at the application task boundary, log tracebacks with `ProjectLogger.exception`, and distinguish a missing result from a successful review or generation.
