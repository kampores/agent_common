# 7.4. Provider Selection and Conditional Local Fallback

[All LLM manuals](01_unified_llm_client_en.md)

> Start with [7.1 Model Profiles and Text Generation](01_model_profiles_and_generation_en.md) for configuration and the minimal call.

## 1. Provider selection and conditional fallback

`LLM_PROVIDER` overrides `provider_str`.

| Provider | Behavior |
| :--- | :--- |
| `external` | External call only; disabled API or missing key returns `None`. |
| `local` | Local inference only. |
| `auto` | Attempts local inference using the same profile only if the external result is `None`. |

HTTP/network errors and missing response fields raise exceptions that propagate to the caller. They do **not** trigger automatic local fallback. An empty string is an external result, not a fallback trigger.

An `auto` profile must contain both external and local settings. It does not discover a second local profile. Add all local loading fields to the external profile and set `provider_str: auto`; token and temperature settings are shared. Keep required profile keys even when using environment overrides, since some configuration defaults are evaluated before environment lookup completes.
