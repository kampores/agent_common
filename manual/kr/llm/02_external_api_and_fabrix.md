# 7.2. 외부 채팅 API 및 Fabrix 연동

[LLM 매뉴얼 전체 목록](01_unified_llm_client.md)

> 설정 준비와 최소 호출은 [7.1 모델 프로필 관리 및 텍스트 생성](01_model_profiles_and_generation.md)을 먼저 참고하세요.

## 1. 외부 API: 표준 형식과 Fabrix

### 표준 채팅 API

`api_format_str: standard`에서는 `base_url_str`과 `chat_completions_path_str`을 결합한 URL로 POST 요청을 보냅니다. Bearer 인증을 사용하며, 요청에는 `model`, `messages`, `max_tokens`, `temperature`가 포함됩니다. 응답은 `choices[0].message.content`에서 읽습니다.

### Fabrix 형식

Fabrix를 사용할 때는 다음 구조로 프로필을 정의합니다. 주소와 모델 식별자는 사용 환경에서 확인한 값으로 교체하세요.

```yaml
llm_pool:
  fabrix_text_generator:
    provider_str: external
    enabled_bool: true
    api_format_str: fabrix_api
    api_key_env_str: X_OPENAPI_TOKEN
    base_url_str: https://your-fabrix-endpoint.example/v1/messages
    llm_id_int: 159
    client_env_str: X_GENERATIVE_AI_CLIENT
    user_env_str: X_CLIENT_USER
    timeout_seconds_int: 120
```

`base_url_str` 자체를 요청 URL로 사용합니다. 인증 키는 `x-openapi-token` 헤더에 넣으며, `client_env_str`과 `user_env_str`에 지정한 환경변수 값이 있으면 각각 `x-generative-ai-client`, `x-client-user` 헤더를 추가합니다.

요청 본문에는 `llmId`, `contents`, `isStream: "False"`를 보내고 응답의 최상위 `content`를 읽습니다. 현재 구현은 Fabrix 요청에 `max_tokens_int`와 `temperature_float`을 전달하지 않습니다. 시스템 프롬프트가 비어 있지 않고 전역 기본 시스템 프롬프트와 다를 때만 사용자 프롬프트 앞에 붙입니다.
