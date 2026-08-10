# agent_common 패키지

중앙 에이전트 및 데이터 이관/생성 서비스를 위한 공통 로깅, 설정 로더, 인프라 클라이언트 및 에러 처리 라이브러리 패키지입니다.

---

## 📌 주요 제공 기능

1. **설정 로더 (`agent_common.config_loader`)**
   - 계층적 YAML 설정 파싱 및 병합 (Deep Merge)
   - 패키지 내 기본 설정(`agent_common/config/*.yml`)과 개별 프로젝트 설정 오버라이드 지원
   - `setting("key.path")` 형태의 점 표기법 설정 조회 기능 및 `NO_PROXY` 자동 반영

2. **단일 행 로깅 포매터 및 로거 (`agent_common.logger`)**
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

### 📦 Wheel 패키지 빌드 (.whl 생성)

새로운 버전으로 패키징하여 `.whl` 파일을 빌드할 경우 `agent_common` 디렉터리 내에서 아래 명령을 실행합니다.

#### 1. 사내 폐쇄망 환경 (인터넷 차단, 완전히 오프라인 빌드)
폐쇄망에서는 외부 PyPI 접속을 완전히 차단하기 위해 `--no-index` 옵션과 빌드 도구 격리 방지(`--no-build-isolation`), 의존성 설치 제외(`--no-deps`) 옵션을 함께 지정합니다.

```bash
# 루트 디렉터리에서 실행 시 (권장)
pip wheel ./agent_common --no-index --no-build-isolation --no-deps -w whls/

# agent_common 디렉터리 내부에서 실행 시
pip wheel . --no-index --no-build-isolation --no-deps -w ../whls/
```

#### 2. 인터넷 연동망 환경 (온라인 빌드)

* **방법 A: `pip wheel` 이용**
  ```bash
  pip wheel . --no-deps -w dist/
  ```

* **방법 B: `build` 모듈 이용**
  ```bash
  # build 도구 설치 (최초 1회)
  pip install build

  # Wheel (.whl) 빌드
  python -m build --wheel
  ```

* **방법 C: `uv` 이용**
  ```bash
  uv build --wheel
  ```

*빌드가 완료되면 `dist/` 디렉터리에 `agent_common-0.2.3-py3-none-any.whl` 파일이 생성됩니다. 생성된 `.whl` 파일은 폐쇄망 배포용 `whls/` 폴더로 복사하여 사용할 수 있습니다.*

### Editable 모드 설치 (개발 환경)
```bash
pip install -e agent_common
```

### Wheel 패키지 설치 (폐쇄망 환경)
```bash
pip install whls/agent_common-0.2.3-py3-none-any.whl
```

---

## 📋 버전 변경 이력 (Changelog)

### v0.3.27 (2026-08-10)
- **`logging_messages.yml` 내 `json_process_error` 템플릿 기본 패키지 내 탑재**:
  - `agent_common/config/logging_messages.yml` 내 `json_process_error` 로그 포맷 템플릿(`"게시판 JSON 메타데이터 {stage} 실패: [JSON_Key={json_key}], 에러: {error}"`) 탑재로 템플릿 미인식 예외 방지

### v0.3.26 (2026-08-10)
- **`ConfigLoader` 로드 파일별 키 수집 트레이서(`_loaded_files_summary`) 및 `.yaml` 확장자 수집 지원 강화**:
  - `config_dir` 디렉터리 내 실제로 파싱하여 읽어들인 파일별 경로명과 각 파일 내부 최상위 키(`loaded_files: [config.yml:['ecs', 'gcs', ...]]`)를 추적하여 로그에 직관적으로 명시
  - `.yml` 뿐만 아니라 `.yaml` 확장자 파일까지 자동 수집 대상 포함

### v0.3.25 (2026-08-10)
- **`ConfigLoader` 클래스 메소드 몽키패칭 결함 제거 및 인스턴스 격리화 완료**:
  - 기존 `ConfigLoader` 클래스 메소드가 모듈 로드 시점의 `_default_loader` 싱글톤으로 강제 몽키패칭되어 모듈 로드 초기 빈 캐시가 인스턴스 전체에 고정되던 결함 전면 수정
  - 인스턴스 단위 독립 캐시(`_cached_settings`) 전환으로 동적 `config.yml` 읽기 및 설정값 파싱의 100% 신뢰성 확보

### v0.3.24 (2026-08-10)
- **`ConfigLoader._find_project_root` 탐색 엔진 3중 안전 강화 (심볼릭 링크 및 메인 스크립트 위치 자동 추적)**:
  - 심볼릭 링크(`link`) 미해제 원본 경로 및 `resolve()` 해제 경로 이중 수집
  - `sys.argv[0]`(실행 스크립트 예: `app/ecs_to_gcs.py`)의 상위 디렉터리(`app/..` = 프로젝트 루트) 우선 추적을 통해 어느 폴더 위치나 배포 환경에서도 `config/config.yml`을 100% 탐지하도록 보정

### v0.3.23 (2026-08-10)
- **`ConfigLoader` 및 클라이언트 오류 로그 내 전체 탐색 후보 경로 목록(`SEARCHED_CANDIDATES`) 직관적 출력 지원**:
  - Fail-Fast 작동 및 설정값 누락 시 `ConfigLoader`가 디스크 상에서 추적하고 체크한 모든 후보 `config/config.yml` 경로 목록과 실제 파일 존재 여부(`[존재함]` / `[없음]`)를 단일 행 로그로 명확히 출력하도록 디버깅 직관성 획기적 강화

### v0.3.22 (2026-08-10)
- **`EcsClient`, `GcsClient`, `BigQueryClient` 내 `logger` 지연 프로퍼티(Lazy Property) 적용**:
  - 클라이언트 객체 생성 초기화(`__init__`) 중 예외 발생 시 `AttributeError: 'GcsClient' object has no attribute 'logger'` 가 발생하는 방어적 결함 100% 원천 차단
  - `@property logger` getter/setter 백킹 필드를 적용하여 초기화 시점과 관계없이 언제나 안전한 `ProjectLogger` 인스턴스 참조 보장

### v0.3.21 (2026-08-10)
- **`agent_common` 플랫 레이아웃(Flat Layout) 전환 및 `package-dir = {"agent_common" = "."}` 지정**:
  - `src/` 중복 폴더 구조를 전면 제거하고 `agent_common/` 루트 폴더 기반 플랫 레이아웃으로 개편
  - `agent_common/config/logging_messages.yml` 파일이 패키지 루트 디렉터리에 직접 위치하면서 `package-dir = {"agent_common" = "."}` 설정만으로 Wheel (`.whl`) 빌드 시 사전 데이터가 100% 깔끔하게 포함되도록 완전 단일화

### v0.3.20 (2026-08-10)
- **`logging_messages.yml` 패키지 데이터 번들링 및 Wheel 배포 누락 문제 근본 해결**:
  - 기존 `agent_common/config/logging_messages.yml`이 `src/` 외부에 위치하여 Wheel (`.whl`) 빌드 시 패키지 배포 파일에서 누락되었던 문제 해결
  - `agent_common/src/config/logging_messages.yml` 패키지 내부 배치 및 `pyproject.toml` 내 `package-data` 빌드 설정 지정을 통해 폐쇄망 환경 배포 시 템플릿 사전 파일이 100% 동봉되도록 개편

### v0.3.19 (2026-08-10)
- **`ProjectLogger.get_log_msg` SafeDict 적용 및 단순 딕셔너리 키 이름 출력 방지**:
  - `logging_messages.yml` 미등록 코드 호출 시 단순 YAML 내부 키(`fail_fast_config_missing` 등)만 덩그러니 출력되던 현상을 정제된 기본 오류 안내 문구로 치환하도록 개선
  - 포맷팅 인자(`kwargs`) 누락 시에도 `SafeDict`를 적용하여 `KeyError` 없이 안전 포맷팅 보장

### v0.3.18 (2026-08-10)
- **`ConfigLoader.require_setting` Fail-Fast 로그 내 절대 파일 경로 및 실체 존재 여부 추적 강화**:
  - `require_setting` 실패 시 단순 파일명만 출력하는 대신 탐색한 실제 절대 경로 및 파일 존재 여부(`[파일 존재함]` / `[파일 없음]`)를 로그 및 `sys.stderr`에 명확히 기록하여 디버깅 직관성 향상

### v0.3.17 (2026-08-10)
- **`ConfigLoader.ROOT` 동적 루트 디렉터리 탐색(`_find_project_root`) 기능 구현**:
  - 하위 폴더(예: `app/`, `scripts/`)에서 스크립트 실행 시 `os.getcwd()`를 그대로 사용하여 `config/` 디렉터리를 찾지 못하고 `fail_fast_config_missing` 오류가 발생하는 문제를 해결하기 위해, 상위 디렉터리를 자동 추적하여 `config/config.yml`이 위치한 메인 프로젝트 루트 경로를 감지하도록 보정

### v0.3.16 (2026-08-10)
- **`ConfigLoader.require_setting` 주요 키 설명 사전(`DEFAULT_KEY_DESCRIPTIONS`) 구축 및 자동 안내 기능 추가**:
  - `require_setting(key)` 단일 인자 호출 시에도 누락된 설정의 한글 설명(`desc_info`)이 로그 및 CLI에 자동으로 결합 출력되도록 개선

### v0.3.15 (2026-08-10)
- **`ProjectLogger.get_log_msg` 템플릿 포맷팅 안전성 강화 및 Fail-Fast 키 상세 정보 유실 방지**:
  - `kwargs` 내 포함된 중괄호(`{ }`)로 인한 `KeyError`/`ValueError` 시 템플릿 문자열이 미치환된 채 출력되는 원인 해결 (자동 중괄호 이스케이프 지원)
  - 템플릿 포맷팅 예외 또는 미등록 코드 반환 시 `kwargs` 상세 파라미터(`path`, `desc_info`, `config_file` 등)가 유실되지 않도록 1줄 상세 정보 결합 보존 지원

### v0.3.14 (2026-08-10)
- **룰 평가 및 템플릿 처리 로깅 템플릿 사전(`logging_messages.yml`) 신설 및 표준 로깅 전면 적용**:
  - `logging_messages.yml` 내 `rule` 섹션 (`rule_eval_success`, `rule_eval_failed`, `rule_not_found`) 신설
  - `app/rule_evaluator.py` 내 하드코딩된 로그 출력을 `ProjectLogger` 템플릿 코드 호출 방식으로 전면 개편

### v0.3.13 (2026-08-10)
- **`ConfigLoader` 설정 디렉터리 접근자/설정자(`config_dir_get`, `config_dir_set`) 도입 및 `ProjectLogger` 설정 로더 바인딩 개편**:
  - `ConfigLoader` 클래스에 `config_dir_get()` (Getter) 및 `config_dir_set(config_dir)` (Setter) 메소드와 `@property`(`config_dir`)를 추가하여 자바 스타일 객체지향 캡슐화 구현
  - `ProjectLogger.__init__` 및 `configure()`에서 `ConfigLoader` 인스턴스를 매번 새로 생성하는 대신 기본 생성 후 `self.config_loader.config_dir_set(config_dir)` 메소드를 통해 설정 디렉터리를 세팅하도록 개선

### v0.3.12 (2026-08-10)
- **`ProjectLogger` 표준 로깅 메서드(`info`, `warning`, `error`, `critical`, `debug`, `exception`) 사전 템플릿 통합 개편**:
  - 기존 `logger.log_msg("LEVEL", "code", **kwargs)` 방식의 번거로운 첫 번째 인자 지정 방식을 개편
  - 파이썬 표준 로깅 메서드(`logger.info("code", **kwargs)`, `logger.error("code", **kwargs)` 등)가 사전 템플릿 코드 자동 조회 및 포맷팅된 메시지 반환(`str`)을 지원하도록 통합
  - 예외 발생 시 `raise ConnectionError(logger.error("code", **kwargs))` 형태로 1줄 깔끔 로깅 + 예외 객체 생성이 가능하도록 개선

### v0.3.11 (2026-08-09)
- **`ProjectLogger` 정석 Adapter 패턴 및 2줄 분리 로깅 구조 전면 적용**:
  - `ProjectLogger(name)` 클래스를 생성자 직접 호출 가능한 Logger Adapter 패턴으로 전면 리팩토링 및 `self.logger.log_msg(...)` 지원
  - `ProjectLogger.get_logger(...)` 팩토리 호출 대신 직관적인 `ProjectLogger(...)` 생성자 직접 호출 구조로 전 프로젝트 표준화
  - `logging_messages.yml` 내 `performance.elapsed_time` 템플릿 신설 및 **[1줄: 작업 수행 결과]**, **[2줄: 범용 작업 소요시간]** 2줄 분리 로깅 구조 적용

### v0.3.10 (2026-08-09)
- **`api_missing_result` $\rightarrow$ `api_missing_field` 동적 필드명 파라미터화**:
  - 특정 필드명(`result`) 하드코딩 문구를 동적 `{field_name}` 파라미터형 범용 키(`api_missing_field`)로 전환하여 API별 응답 필드(예: `choices[0].message.content`, `content`, `data`) 파싱 오류를 유연하게 로깅

### v0.3.9 (2026-08-09)
- **`agent_common/src/llm.py` 표준 로깅 개편**:
  - `LlmClient` 소스코드 내 하드코딩된 로깅/예외 문구를 `get_log_msg` 표준 사전 메시지(`api_call_started`, `api_disabled`, `api_key_missing`, `api_call_success`, `api_http_error`, `api_connection_error`, `api_missing_result`)로 전면 개편

### v0.3.8 (2026-08-09)
- **`ERROR: service:` 영역 레거시 키 정제 및 범용 HTTP/REST API 템플릿화**:
  - 레거시 특정 명칭(`llm_`, `runner_`) 키들을 정제하여 범용 HTTP/REST API 서비스 키(`api_http_error`, `api_connection_error`, `api_unexpected_error`, `api_missing_result`)로 일원화

### v0.3.7 (2026-08-09)
- **`storage_meta_error` 에러 영역 이동 및 `get_log_msg` 레벨 전역 유연화**:
  - `storage_meta_error` 템플릿을 본질에 맞춰 `WARNING` $\rightarrow$ `ERROR: storage:` 섹션으로 이동
  - `get_log_msg` 탐색 로직을 전역 레벨 다중 검색 구조로 확장하여, 호출 측 도메인 상황에 맞게 `WARNING` 또는 `ERROR` 레벨로 자유롭게 호출 가능하도록 지원

### v0.3.6 (2026-08-09)
- **로깅 메시지 사전 중분류(Sub-category) 계층화 및 `get_log_msg` 탐색 자동화**:
  - `logging_messages.yml` 사전 내 메시지들을 도메인 중분류(`lifecycle`, `storage`, `fallback`, `permission`, `config`, `service`, `system`) 그룹으로 구조화
  - `get_log_msg` 헬퍼 함수 개편으로 기존 직속 레벨 키 탐색 실패 시 하위 중분류 카테고리 딕셔너리를 자동 재귀 검색하도록 지원

### v0.3.5 (2026-08-09)
- **로깅 템플릿 사전(`agent_common/config/logging_messages.yml`) 소스코드 호출 가이드 및 주석 강화**:
  - 개발자가 타 서비스 개발 시 템플릿 키를 손쉽게 활용할 수 있도록 모듈 가이드 헤더 및 각 키별 Python `get_log_msg("LEVEL", "code", **kwargs)` 사용 예시 주석 추가

### v0.3.4 (2026-08-08)
- **시스템 전역 범용 로그 메시지 템플릿 사전(`agent_common/config/logging_messages.yml`) 이관 및 확장**:
  - 특정 스토리지/도메인 명칭(ECS 등)이 하드코딩되지 않도록 파라미터형 범용 템플릿(`client_init_failed`, `program_started`, `program_finished`, `sync_started`, `sync_completed`, `folder_searching`, `no_target_files`, `targets_detected`, `fallback_applied`, `regex_compile_error`)으로 정제하여 공용 패키지로 이관 반영

### v0.3.3 (2026-08-08)
- **`ConfigLoader` 클래스 캡슐화 및 동적 로거 명칭 적용**:
  - `config_loader.py` 모듈 내 설정 로드 및 검증 함수들을 `ConfigLoader` 클래스로 캡슐화(객체지향 설계 준수 및 하위 호환 모듈 별칭 유지)
  - 필수 설정 검증(`require_setting`) 시 하드코딩된 로거 이름 대신 `ProjectLogger.get_logger(f"agent_common.{cls.__name__}")`를 활용하여 클래스 명칭(`agent_common.ConfigLoader`)이 동적으로 로거 이름에 반영되도록 개선

### v0.3.2 (2026-08-08)
- **로그 레벨별 메시지 템플릿 사전(`logging_messages.yml`) 구축 및 `errors.yml` 통합**:
  - 기존 `errors.yml`을 `logging_messages.yml`의 `ERROR` 영역으로 수용 통합하고 `INFO`, `WARNING`, `ERROR`, `CRITICAL` 레벨별 로그 메시지 템플릿 사전 체계 구축
- **동적 템플릿 로깅 조작 함수(`get_log_msg`) 신설**:
  - `agent_common.logger.get_log_msg(level, code, **kwargs)`: 메시지 코드 및 동적 인자를 수신하여 템플릿 문장을 포맷팅 반환하며 하드코딩 문구 전면 제거

### v0.3.1 (2026-08-08)
- **`EcsClient.transfer_to_gcs` 파일 전송 및 통합 로깅 공통 메소드 신설**:
  - Dell ECS S3 스토리지에서 Google Cloud Storage(GCS)로의 실시간 스트리밍 파일 전송, GCS 기존 중복 용량 검사(Skip), 구간별 소요 시간 측정(`TotalElapsed`, `CheckTime`, `ECSStreamTime`, `GCSUploadTime`) 및 단일 행 표준 로깅을 공통 인프라 메소드로 일원화
- **인프라 클라이언트(`EcsClient`, `GcsClient`, `BigQueryClient`) 로깅 표준화 통일**:
  - `logger` 및 `error_messages` 파라미터를 선택적(Optional)으로 처리하고, 미지정 시 `ProjectLogger.get_logger()`의 표준 1줄 포매터 로거가 자동으로 결합되도록 표준화 일원화

### v0.3.0 (2026-08-08)
- **Fail-Fast 정책 지원 필수 설정 검증 메소드(`require_setting`) 신설**:
  - `config_loader.require_setting(path, message, config_file, logger)`: 필수 설정값이 누락되거나 빈 값일 경우 코드 내 상수로 대체하지 않고, 대상 설정 파일명과 함께 에러 메시지를 CLI(`sys.stderr`) 및 표준 로거(`logging.getLogger()`)로 출력한 뒤 프로세스를 강제 종료(`sys.exit(1)`)하도록 구현하여 빠른 실패(Fail-Fast) 정책 반영

### v0.2.9 (2026-07-29)
- **BigQuery 적재 시 최초 1회 배치 실패 후 스트리밍 전용 모드 자동 전환**:
  - `BigQueryClient`: 권한 부족(`bigquery.jobs.create`) 등으로 `load_table_from_json` 실패 시 `self._use_streaming_only = True`로 전환하여, 이후 요청부터는 배치 로드 시도 및 중복 경고(WARNING) 로그 없이 `insert_rows_json` 스트리밍 적재를 직행하도록 개선

### v0.2.8 (2026-07-29)
- **예외 발생 원천 위치([Origin: filename:Llineno in funcName()]) 자동 추적 강화**:
  - `SingleLineFlattenFormatter`: `record.exc_info` 처리 시 Traceback의 최후 발생 프레임을 분석하여 **예외가 처음 발생한 실제 원천 파일명, 줄 번호, 함수명**(`[Origin: filename:Llineno in funcName()]`)을 로그 서두에 자동 결합하여 기록하도록 개선

### v0.2.7 (2026-07-29)
- **로깅 실행 위치(파일명, 라인번호, 함수명) 및 BigQuery Sub-error Tracing 강화**:
  - `SingleLineFlattenFormatter` / `ProjectLogger`: 기본 로그 포맷에 `[%(filename)s:%(lineno)d %(funcName)s()]` 정보를 추가하여 모든 로그에 실행 위치 자동 기록
  - `BigQueryClient.insert_json_data`: `load_table_from_json` (배치 로드) 실패 시 `load_job.errors` 배열 내의 필드별 세부 에러 위치(`location`) 및 사유 메시지를 1줄로 추적 로깅하도록 개선

### v0.2.6 (2026-07-28)
- **BigQuery 적재 로직 Fallback 전환 구조 반영**: `BigQueryClient.insert_json_data` 호출 시 배치 적재(`load_table_from_json`)를 우선 수행하고 예외 발생 시 스트리밍 적재(`insert_rows_json`)로 자동 fallback 하도록 안정성 개선

### v0.2.5 (2026-07-27)
- **BigQuery Native JSON 타입 스키마 바인딩**: `insert_rows_json` 호출 시 `Table` 객체를 전달하여 BigQuery Native `JSON` 컬럼을 SDK가 `RECORD`로 오인하지 않고 정상 인코딩하도록 스키마 사전 바인딩 개선

### v0.2.4 (2026-07-27)
- **BigQuery 적재 실패 필드 상세 로깅 강화**: `insert_rows_json` API 반환 오류 시 `location`(실패 필드명), `reason`, `message`를 명확히 1줄로 통합 출력하도록 개선

### v0.2.3 (2026-07-27)
- **BigQuery 기존 적재 키 조회 지원**: `BigQueryClient.get_existing_keys(field_name)` 메소드 추가로 중복 데이터 적재 사전 검사 및 Skip(건너뛰기) 성능 최적화 제공

### v0.2.2 (2026-07-21)
- **타임아웃(`transfer.timeout_seconds`) 바인딩**: `EcsClient`(boto3 connect/read), `GcsClient`(upload/get_blob), `BigQueryClient`(insert_rows_json)에 네트워크 연결 및 데이터 읽기 타임아웃 지원
- **Fail-Fast 정책 강화**: `timeout_seconds` 설정 누락 시 코드 상수로 fallback(하드코딩)하지 않고, 초기 가동 시점에 에러 출력 후 즉시 종료하도록 구현
- **GCS 메타데이터 크기 조회 지원**: `GcsClient.get_blob_size()`를 통한 동일 용량 파일 중복 이관 건너뛰기(Skip) 로직 제공

### v0.2.1 (2026-07-20)
- **에러 메시지 사전 통합**: 파일 전송, ECS, GCS, BigQuery 공통 에러 메시지 템플릿을 `agent_common/config/errors.yml`로 통합 배치
- **설정 로더 경로 보정**: `config_loader.py`의 `PACKAGE_DIR` 탐색 경로를 패키지 루트 디렉토리로 보정하여 공통 `errors.yml` 자동 병합 지원

### v0.2.0 (2026-07-20)
- **인프라 클라이언트 모듈 신설**: `agent_common.clients` 모듈에 `EcsClient`, `GcsClient`, `BigQueryClient` 포함
- **단일 행 로깅 포매터 승격**: `SingleLineFlattenFormatter` 클래스를 공용 모듈로 승격하고 `ProjectLogger.configure()`에 기본 포매터로 연결
- **1줄 평탄화 메소드명 추가**: `flatten_to_single_line()` 헬퍼 메소드 추가

### v0.1.0 (2026-06-18)
- **초기 릴리즈**: 기본 `config_loader`, `logging_config`, `error_handler`, `llm` 패키지 구성
