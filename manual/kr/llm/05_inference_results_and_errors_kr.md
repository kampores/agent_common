# 7.5. 추론 결과 및 예외 처리

[LLM 매뉴얼 전체 목록](01_unified_llm_client_kr.md)

> 설정 준비와 최소 호출은 [7.1 모델 프로필 관리 및 텍스트 생성](01_model_profiles_and_generation_kr.md)을 먼저 참고하세요.

## 1. 반환값과 예외 처리

| 상황 | 현재 동작 | 확인할 항목 |
| :--- | :--- | :--- |
| 모델 프로필 미등록 | 생성자에서 `LlmInferenceError` | `llm_pool` 키와 모델 선택 설정 |
| 지원하지 않는 provider | `LlmInferenceError` | `auto`, `external`, `local` 중 하나인지 확인 |
| 외부 비활성화·API 키 누락 | 외부 경로에서 `None` | 활성화 설정과 인증 환경변수 |
| HTTP·URL 통신 오류 | `LlmInferenceError` | 서버 응답, 주소, 인증, 네트워크 |
| 필수 응답 필드 누락 | `LlmInferenceError` | 표준/Fabrix 형식과 실제 응답 구조 |
| 로컬 파일 미존재 | `None` | 프로젝트 루트 기준 파일 경로 |
| 로컬 라이브러리 미설치 | 모델 파일 존재 시 `LlmInferenceError` | 실행 환경의 의존성 |
| JSON 파싱, 숫자 변환, 일부 타임아웃·모델 실행 오류 | 원래 예외가 전달될 수 있음 | `LlmInferenceError`만으로 모든 실패를 처리할 수 있다고 가정하지 않기 |

호출 애플리케이션은 `None`과 예외를 구분해 처리해야 합니다. 작업 처리 경계에서 명시적인 예외를 우선 처리하고, 마지막에 예상하지 못한 예외를 처리하여 다음 작업을 계속할지 결정합니다. 예외 로그에는 `ProjectLogger`의 `logger.exception`을 사용합니다.
