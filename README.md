# agent_common 패키지

중앙 에이전트 및 데이터 이관/생성 서비스를 위한 공통 로깅, 설정 로더, 인프라 클라이언트 및 에러 처리 라이브러리 패키지입니다.

---

## 📌 주요 제공 기능

1. **설정 로더 (`agent_common.config_loader`)**
   - 계층적 YAML 설정 파싱 및 병합 (Deep Merge)
   - 패키지 내 기본 설정(`agent_common/config/*.yml`)과 개별 프로젝트 설정 오버라이드 지원
   - `setting("key.path")` 형태의 점 표기법 설정 조회 기능 및 `NO_PROXY` 자동 반영

2. **단일 행 로깅 포매터 및 로거 (`agent_common.logging_config`)**
   - `SingleLineFlattenFormatter`: 모든 로그 및 Traceback 예외 메시지를 1줄로 평탄화하여 중앙 로그 수집(Logstash, Fluentd 등)에 최적화
   - `ProjectLogger`: 콘솔 및 파일 로그 핸들러 동적 생성 및 일자별 로그 분리 관리

3. **스토리지 및 데이터베이스 클라이언트 (`agent_common.clients`)**
   - `EcsClient`: Dell ECS S3 저장소 접속, 목록 조회 및 파일 스트리밍 획득
   - `GcsClient`: Google Cloud Storage 연결 및 파일 스트리밍 업로드
   - `BigQueryClient`: Google Cloud BigQuery 연결 및 JSON 데이터 스트리밍 입력(`insert_rows_json`)

4. **공용 에러 및 예외 핸들러 (`agent_common.error_handler`)**
   - 네트워크 장애, 설정 오류, 런타임 예외에 대한 일관된 로깅 및 핸들링 제공

---

## 🚀 설치 및 사용 방법

### Editable 모드 설치 (개발 환경)
```bash
pip install -e agent_common
```

### Wheel 패키지 설치 (폐쇄망 환경)
```bash
pip install whls/agent_common-0.2.1-py3-none-any.whl
```

---

## 📋 버전 변경 이력 (Changelog)

### v0.2.1 (2026-07-20)
- **에러 메시지 사전 통합**: 파일 전송, ECS, GCS, BigQuery 공통 에러 메시지 템플릿을 `agent_common/config/errors.yml`로 통합 배치
- **설정 로더 경로 보정**: `config_loader.py`의 `PACKAGE_DIR` 탐색 경로를 패키지 루트 디렉토리로 보정하여 공통 `errors.yml` 자동 병합 지원

### v0.2.0 (2026-07-20)
- **인프라 클라이언트 모듈 신설**: `agent_common.clients` 모듈에 `EcsClient`, `GcsClient`, `BigQueryClient` 포함
- **단일 행 로깅 포매터 승격**: `SingleLineFlattenFormatter` 클래스를 공용 모듈로 승격하고 `ProjectLogger.configure()`에 기본 포매터로 연결
- **1줄 평탄화 메소드명 추가**: `flatten_to_single_line()` 헬퍼 메소드 추가

### v0.1.0 (2026-06-18)
- **초기 릴리즈**: 기본 `config_loader`, `logging_config`, `error_handler`, `llm` 패키지 구성
