# 7.4. 실행 모드 및 조건부 로컬 전환

[LLM 매뉴얼 전체 목록](01_unified_llm_client_kr.md)

> 설정 준비와 최소 호출은 [7.1 모델 프로필 관리 및 텍스트 생성](01_model_profiles_and_generation_kr.md)을 먼저 참고하세요.

## 1. 실행 모드와 조건부 로컬 전환

`LLM_PROVIDER` 환경변수가 있으면 프로필의 `provider_str`보다 우선합니다.

| 모드 | 동작 |
| :--- | :--- |
| `external` | 외부 호출만 수행. 비활성화 또는 API 키 누락 시 `None` 반환 |
| `local` | 로컬 모델만 실행 |
| `auto` | 외부 호출 결과가 `None`일 때 같은 프로필의 로컬 설정으로 실행 |

**`auto`는 모든 외부 장애에 대한 자동 복구를 의미하지 않습니다.** 외부 호출이 `HTTPError`, `URLError` 또는 필수 응답 필드 오류로 예외를 발생시키면 로컬로 넘어가지 않고 예외가 호출자에게 전달됩니다. 빈 문자열도 `None`이 아니므로 외부 응답으로 반환합니다.

`auto`를 쓰려면 **하나의 프로필에 외부 설정과 로컬 설정을 함께** 정의해야 합니다. 별도의 로컬 프로필을 자동으로 찾지 않습니다. [7.1의 `text_generator` 프로필](01_model_profiles_and_generation_kr.md)에 [7.3 로컬 예시](03_local_gguf_inference_kr.md)의 `model_path_str`, `n_ctx_int`, `n_threads_int`, `n_batch_int`, `n_gpu_layers_int`, `verbose_bool`을 추가하고 `provider_str`을 `auto`로 바꾸세요. `max_tokens_int`와 `temperature_float`은 해당 프로필에서 공유합니다.

기본 외부 전용 프로필에 `LLM_PROVIDER=auto`만 지정하면 로컬 설정이 부족할 수 있습니다. 환경변수로 경로 등을 지정하더라도 코드가 설정값을 기본 인자로 먼저 평가하는 항목이 있으므로, 필요한 프로필 키 자체를 생략하지 마세요.
