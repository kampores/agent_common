# 7. 통합 LLM 클라이언트 및 추론 엔진 (`LlmClient`)

> **소속 모듈**: `agent_common.llm`  
> **공개 API**: `LlmClient`, `LlmInferenceError`  
> **설정 파일**: `config/config.yml`, `config/llmpool.yml`  
> **구현 기준**: 저장소의 `src/agent_common/llm.py`

필요한 기능 번호의 매뉴얼부터 참고하세요. 먼저 7.1의 최소 호출을 확인한 다음 외부 API, 로컬 모델, 오류 처리 등을 단계적으로 적용합니다. Groq 감독관 AI 사례는 7.6에 있습니다.

- **[7.1. 모델 프로필 관리 및 텍스트 생성](01_model_profiles_and_generation_ko.md)**
- **[7.2. 외부 채팅 API 및 Fabrix 연동](02_external_api_and_fabrix_ko.md)**
- **[7.3. 로컬 GGUF 추론 및 모델 캐싱](03_local_gguf_inference_ko.md)**
- **[7.4. 실행 모드 및 조건부 로컬 전환](04_provider_and_local_fallback_ko.md)**
- **[7.5. 추론 결과 및 예외 처리](05_inference_results_and_errors_ko.md)**
- **[7.6. Groq 감독관 AI 및 Antigravity Stop 훅](06_groq_supervisor_and_stop_hook_ko.md)**
