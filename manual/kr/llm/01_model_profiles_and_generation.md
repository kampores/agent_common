# 7.1. 모델 프로필 관리 및 텍스트 생성

[LLM 매뉴얼 전체 목록](01_unified_llm_client.md)

## 1. 개요와 권장 구현 순서

`LlmClient`는 외부 채팅 API와 로컬 GGUF 모델을 같은 `generate()` 인터페이스로 호출합니다. 텍스트 요약, 분류, SQL 문자열 생성 등에 활용할 수 있습니다. SQL 실행이나 대화 이력 저장은 수행하지 않으며, 매 호출에 시스템 메시지와 사용자 메시지를 전달합니다.

처음에는 **하나의 모델로 프롬프트를 보내고 응답을 받는 최소 기능**부터 구현하세요. 응답을 확인한 다음 용도별 모델 선택, 로컬 실행, 조건부 전환 등을 필요한 순서대로 추가합니다. 설정 로더의 변수형 보증(README 1.3)과 `config` 점 표기법(1.2)을 애플리케이션 전체에 적용하는 작업도 단계적으로 진행할 수 있습니다.

## 2. 설정 준비와 최소 호출

Python 3.10 이상과 `agent-common` 패키지가 필요합니다. 외부 API 호출에는 Python 표준 라이브러리 `urllib.request`를 사용합니다. 로컬 GGUF 실행에는 별도로 `llama-cpp-python`과 모델 파일이 필요하며, 현재 패키지의 `all` 추가 의존성에도 `llama-cpp-python`은 포함되어 있지 않습니다.

프로젝트의 `config/config.yml`과 `config/llmpool.yml`을 먼저 준비한 뒤 실행하세요. 패키지 기본 설정과 프로젝트 설정은 `ConfigLoader`를 통해 병합됩니다. 아래 값은 사용자 환경에 맞게 지정해야 하는 예시이며, API 키 값은 YAML에 넣지 않고 환경변수로 전달합니다.

`config/config.yml`:

```yaml
llm:
  default_purpose_str: sql_generator
  sql_generator_model_str: text_generator
  router_model_str: text_generator
  system_prompt_str: 요청에 한국어로 간결하게 답하세요.

generation_request:
  prompt_str: 데이터 이관 작업의 목적을 한 문장으로 설명해줘.
```

`config/llmpool.yml`:

```yaml
llm_pool:
  text_generator:
    provider_str: external
    enabled_bool: true
    api_format_str: standard
    api_key_env_str: EXTERNAL_LLM_API_KEY
    base_url_str: https://your-llm-endpoint.example/v1
    chat_completions_path_str: /chat/completions
    model_str: your-server-model-name
    timeout_seconds_int: 60
    max_tokens_int: 512
    temperature_float: 0.0
```

`base_url_str`과 `model_str`을 실제 서버 주소와 모델명으로 바꾸고, 실행 환경에 `EXTERNAL_LLM_API_KEY`를 설정합니다. 위 설정을 준비한 후 최소 호출은 다음과 같습니다.

```python
from agent_common.config_loader import config
from agent_common.llm import LlmClient

llm_client_obj = LlmClient()
response_str = llm_client_obj.generate(
    prompt_str=config.generation_request.prompt_str,
)
```

`response_str`은 생성된 문자열 또는 `None`입니다. 호출자가 응답 저장·표시를 담당하고, [7.5 반환값 및 예외 규칙](05_inference_results_and_errors.md)에 따라 작업 결과를 처리합니다. 위 코드는 설정을 준비한 뒤 호출하는 최소 예시입니다. 실행 프로그램의 설정 자동 생성·기본 스키마 등록은 [1.6 설정 파일 자동 생성](../config_loader/06_ensure_config_self_healing.md)을 참고하세요.

## 3. 모델 선택과 공개 API

### `LlmClient(model_name_str=None, purpose_str=None, config_dir_path=None)`

| 인자 | 의미 |
| :--- | :--- |
| `model_name_str` | `llm_pool` 아래의 프로필 키. 지정하면 용도별 모델 선택보다 우선합니다. 서버에 보내는 `model_str`과 구분합니다. |
| `purpose_str` | 미지정 시 전역 `config.llm.default_purpose_str`. `router`이면 `router_model_str`, 그 외에는 `sql_generator_model_str`을 사용합니다. |
| `config_dir_path` | 인스턴스가 모델 프로필을 읽는 설정 디렉터리. 미지정 시 프로젝트의 `config` 디렉터리입니다. |

임의의 `purpose_str`을 추가한다고 같은 이름의 설정 키를 자동 탐색하지는 않습니다. 새로운 용도에는 `model_name_str`으로 프로필을 명시하는 방법을 사용할 수 있습니다.

`config_dir_path`는 인스턴스의 프로필 조회에 적용됩니다. 기본 용도, 용도별 모델명, 기본 시스템 프롬프트는 여전히 전역 `config.llm`을 참조하므로, 별도 디렉터리만 지정해서 이 값까지 바뀐다고 가정하지 마세요. 필요한 경우 `model_name_str`과 `system_prompt_str`을 명시합니다.

### `generate(prompt_str="", system_prompt_str=None)`

| 항목 | 동작 |
| :--- | :--- |
| `prompt_str` | 사용자 프롬프트 문자열 |
| `system_prompt_str` | `None`이면 전역 `config.llm.system_prompt_str` 사용. 빈 문자열은 그대로 전달 |
| 반환값 | 생성된 문자열 또는 생성 결과가 없을 때 `None` |
| `last_generated_by_str` | 매 호출 시작에 `None`으로 초기화. 성공 시 `external_llm` 또는 `local_llm` |
| `model_config` | 현재 모델 프로필을 읽기 전용 설정 객체로 조회하는 속성 |

생성자에서는 프로필 존재 여부를 확인합니다. API 접속이나 로컬 모델 로딩까지 검증하는 것은 아니며, 해당 작업은 생성 요청 시 실행됩니다.

## 4. 환경변수 우선순위

| 범위 | 환경변수 | 대응 설정 또는 동작 |
| :--- | :--- | :--- |
| 공통 | `LLM_PROVIDER` | `provider_str` 재정의 |
| 외부 공통 | `EXTERNAL_LLM_ENABLED` | `enabled_bool` 재정의. `1`, `true`, `yes`, `on`을 대소문자 구분 없이 활성화로 해석 |
| 외부 공통 | 프로필의 `api_key_env_str`에 지정한 변수 | 먼저 확인하고, 값이 없으면 `EXTERNAL_LLM_API_KEY` 확인 |
| 표준 API | `EXTERNAL_LLM_BASE_URL`, `EXTERNAL_LLM_CHAT_COMPLETIONS_PATH`, `EXTERNAL_LLM_MODEL` | URL, 경로, 서버 모델명 재정의 |
| 표준 API | `EXTERNAL_LLM_MAX_TOKENS`, `EXTERNAL_LLM_TEMPERATURE`, `EXTERNAL_LLM_TIMEOUT_SECONDS` | 생성 옵션과 타임아웃 재정의 |
| Fabrix | `FABRIX_LLM_ID`, `FABRIX_TIMEOUT_SECONDS` | 모델 식별자와 타임아웃 재정의 |
| Fabrix | `client_env_str`, `user_env_str`에 지정한 변수 | 추가 인증 헤더 값 |
| 로컬 | `LOCAL_LLM_MODEL_PATH` | GGUF 파일 경로 |
| 로컬 | `LOCAL_LLM_N_CTX`, `LOCAL_LLM_N_THREADS`, `LOCAL_LLM_N_BATCH`, `LOCAL_LLM_N_GPU_LAYERS` | 모델 로딩 옵션 |
| 로컬 | `LOCAL_LLM_MAX_TOKENS`, `LOCAL_LLM_TEMPERATURE` | 생성 옵션 |
| 로컬 | `LOCAL_LLM_VERBOSE` | 대소문자 구분 없이 `true`일 때 상세 로그 활성화 |

표준 API의 `EXTERNAL_LLM_BASE_URL` 등은 Fabrix 요청 URL이나 생성 옵션에 적용되지 않습니다. 정수·실수 환경변수에 올바르지 않은 문자열을 넣으면 변환 예외가 발생합니다.
