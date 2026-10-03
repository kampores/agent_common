# 7.6. Groq Supervisor and Antigravity Stop Hook

[All LLM manuals](01_unified_llm_client_en.md)

> Start with [7.1 Model Profiles and Text Generation](01_model_profiles_and_generation_en.md) for configuration and the minimal call.

## 1. Practical example: a Groq supervisor for a coding AI

The reference project uses an Antigravity Stop hook to review Python changes made by a coding AI against selected `AGENTS.md` rules. The supervisor calls Groq's `openai/gpt-oss-120b`, then returns approval or a request to correct specific violations. The authoring model and reviewing model have separate roles.

The project files are `.agents/hooks.json` and `scripts/groq_supervisor.py`; they are not included in the installed `agent-common` package. The existing script calls Groq directly through `urllib.request`, rather than using `LlmClient`.

The project's hook configuration is:

```json
{
  "groq-agents-supervisor": {
    "enabled": true,
    "Stop": [
      {
        "type": "command",
        "command": "cmd /c \"if exist .\\venv313\\Scripts\\python.exe ( .\\venv313\\Scripts\\python.exe scripts\\groq_supervisor.py ) else ( cd .. && .\\venv313\\Scripts\\python.exe scripts\\groq_supervisor.py )\"",
        "timeout": 60
      }
    ]
  }
}
```

Adapt virtual environment paths, script paths, and working-directory assumptions for your project. This is a project example, not a claim that every editor supports this hook format.

The script collects `git diff HEAD -- *.py` and untracked Python file contents, excluding the supervisor itself from the untracked-file collection. This covers uncommitted changes since HEAD, not necessarily just the latest assistant turn. It sends those changes with a prompt checking type suffixes, Korean headers/docstrings, shared logging, externalized configuration, no nested functions, and standard-library HTTP clients. The prompt also explains exceptions to avoid false positives on partial diffs and permitted identifiers.

The current script embeds a summary of selected rules; it does not read the live `AGENTS.md` text on every invocation. Rule changes require updating that prompt.

```json
{"decision": "allow", "reason": "AGENTS.md 규칙 검증 통과"}
```

```json
{"decision": "continue", "reason": "수정한 함수 인자에 타입 접미사가 누락되었습니다. 인자와 호출부를 수정하세요."}
```

The script returns JSON on stdout as the hook result. It does not edit files itself. No Python changes produce immediate approval. Missing API keys and API/response failures also return `allow` with a skipped-review reason, so check `reason` before interpreting approval as a completed review.

The input message is truncated after 4,000 characters. Non-Python files are not reviewed. Some errors trigger retries with other external models, a feature implemented in the supervisor rather than `LlmClient.auto`. Each request has a 60-second timeout, while the hook itself also has a 60-second limit; multiple retries may exceed the hook limit.

### Implementing the same role with `LlmClient`

Separate change collection, rule-prompt construction, generation, response validation, and hook output. The packaged `groq_gpt_oss` profile selects Groq, `GROQ_API_KEY`, and `openai/gpt-oss-120b`.

```yaml
llm:
  router_model_str: groq_gpt_oss

supervisor:
  purpose_str: router
```

The following is the generation stage; the two prompt strings must already contain the collected changes and review instructions:

```python
from agent_common.config_loader import config
from agent_common.llm import LlmClient

supervisor_client_obj = LlmClient(purpose_str=config.supervisor.purpose_str)
review_response_str = supervisor_client_obj.generate(
    prompt_str=review_prompt_str,
    system_prompt_str=review_system_prompt_str,
)
```

The current client does not expose the supervisor's `response_format: {"type": "json_object"}` option or external-model retry sequence. Parse and validate JSON, the `decision` and `reason` types, and allowed decisions in the application. Define how `None`, malformed responses, and API failures affect review results. The direct script's disabled certificate validation is also not a `LlmClient` feature.

Start with a small diff and a single model. Add hook integration, full rule coverage, input splitting, and retry policies only after the minimal review works.

## 2. Example request to an AI

```text
Build a Groq supervisor that reviews a coding AI's Python changes against AGENTS.md.
Use https://pypi.org/project/agent-common/ and https://github.com/kampores/agent_common.
Read README sections 7.1, 7.2, 7.5, and 7.6 and their linked manuals.
Start by sending a small diff and review rules to one model and obtaining a decision.
Check the actual API and ask about missing requirements before implementing them.
Validate decision/reason and clarify the policy for failed reviews.
Add the Stop hook and further features after the minimal review works.
```
