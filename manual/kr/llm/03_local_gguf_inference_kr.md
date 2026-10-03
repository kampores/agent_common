# 7.3. 로컬 GGUF 추론 및 모델 캐싱

[LLM 매뉴얼 전체 목록](01_unified_llm_client_kr.md)

> 설정 준비와 최소 호출은 [7.1 모델 프로필 관리 및 텍스트 생성](01_model_profiles_and_generation_kr.md)을 먼저 참고하세요.

## 1. 로컬 GGUF 모델

```yaml
llm_pool:
  local_text_generator:
    provider_str: local
    model_path_str: llm_models/your-model.gguf
    n_ctx_int: 4096
    n_threads_int: 4
    n_batch_int: 512
    n_gpu_layers_int: 0
    max_tokens_int: 512
    temperature_float: 0.0
    verbose_bool: false
```

이 프로필을 사용하려면 `config.yml`의 `llm.sql_generator_model_str`을 `local_text_generator`로 변경합니다.

`model_path_str`에는 준비한 GGUF 파일을 지정합니다. 상대 경로는 설정 파일 디렉터리가 아니라 `ConfigLoader`가 결정한 프로젝트 루트를 기준으로 해석합니다. 파일이 없으면 `generate()`는 `None`을 반환합니다. 파일이 있고 `llama-cpp-python`이 없으면 `LlmInferenceError`가 발생합니다.

`n_ctx_int`는 컨텍스트 크기, `n_threads_int`는 CPU 스레드 수, `n_batch_int`는 프롬프트 처리 배치 크기입니다. `n_gpu_layers_int: 0`은 CPU 실행이며 GPU 사용 가능 여부는 설치한 추론 엔진 빌드와 실행 환경에 달려 있습니다.

모델은 첫 호출 때 로딩하며, 같은 모델 경로의 객체를 프로세스 내에서 재사용합니다. 캐시 키는 모델 경로이므로 동일 경로에서 컨텍스트 크기나 GPU 레이어 등 로딩 설정을 바꿔도 이미 로딩된 객체에는 적용되지 않습니다. 로딩 설정 변경은 프로세스를 다시 시작한 후 확인하세요.
