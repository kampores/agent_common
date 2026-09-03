# 버전 변경 이력 (Changelog)

### v0.4.21 (2026-09-03)
- **`BigQueryClient.merge_table_from_json_data` 기본 청크 크기 하향 및 BigQuery API 413 Payload Too Large 방지**:
  - `chunk_size_int` 기본값을 기존 `500`에서 안전한 `100`으로 하향 조정.
  - BigQuery SQL 쿼리 파라미터(`@json_payload`) 크기 제한(1MB/1,024KB) 초과로 인한 HTTP `413 (Payload Too Large)` 에러를 원천 방지하고 대용량 비정형 메타데이터 MERGE 안정성 확보.
  - 독스트링 기본값 설명 갱신.

### v0.4.20 (2026-09-02)
- **`ProjectLogger` 에러 및 진행 건수 분류(성공/실패/제외) 집계, `log_summary` 요약 리포트 로거 고유 책임(SRP) 이전**:
  - `ProjectLogger.update(success_bool, excluded_bool, count_int)`, `record_result()`, `record_success()`, `record_failure()`, `record_excluded()` 및 `get_result_counts()`를 추가하여 진행 건수 분류 책임을 로거로 일원화.
  - `ProjectLogger.error()`, `exception()`, `critical()`, `log_msg()` 호출 시 로그 ID 및 실패 건수를 내부 `error_counts_dict` / `failure_count_int`에 자동 누적 기록하도록 개선.
  - `logging_messages.yml` 템플릿 탐색 및 한글 설명 정제 메서드 `get_log_id_description()`과 최종 결과 요약 리포트 생성 메서드 `log_summary()`를 `ProjectLogger`의 메서드로 통합.
  - `ProgressTracker.update(count_int=1, bytes_int=0, details_str="")`로 파라미터를 개편하여, `ProgressTracker`는 순수 진행 건수/바이트/진행률(%) 및 마일스톤 판별만 수행하는 경량 트래커로 정돈.
  - 메인 애플리케이션(`ecs_to_gcs.py`, `ecs_to_bigquery.py`, `ecs_to_gcsbigquery_merge.py`)의 트래커/로거 호출 인터페이스 동기화.

### v0.4.19 (2026-09-02)
- **`BigQueryClient.format_timestamp` -> `BigQueryClient.convert_to_bigquery_timestamp` 명칭 직관화 및 표준화**:
  - 다양한 원천 일시 포맷(YYYYMMDD, YYYYMMDDHHMMSS, ISO8601 등)을 BigQuery 표준 타임스탬프(`YYYY-MM-DD HH:MM:SS{tz}`) 문자열로 변환하는 목적을 직관적으로 드러내도록 메서드명을 `convert_to_bigquery_timestamp`로 개선.
  - `table_transformer.py` 등 호출부 및 관련 참조 동기화.

### v0.4.18 (2026-09-01)
- **`BigQueryClient.merge_table_from_json_data` UNNEST SELECT 절 `JSON_VALUE` 직접 반환 및 SQL 타입 분기 보강**:
  - `JSON_VALUE(...)` 반환값에 불필요하게 씌워져 있던 `STRING(...)` 함수 래핑을 제거하여 `400 No matching signature for function STRING` 쿼리 구문 오류 원천 해결.
  - 명시적 컬럼 타입 매핑(`column_types_dict`) 지원 시 `DATETIME`, `DATE`, `TIME`, `INT/BIGINT/NUMERIC/FLOAT` 등의 다양한 SQL 타입 캐스팅 표현식(`DATETIME(...)`, `DATE(...)`, `TIME(...)`, `SAFE_CAST(...)`) 분기 보강.

### v0.4.17 (2026-09-01)
- **`BigQueryClient.merge_table_from_json_data` 컬럼명 및 식별자 백틱(`` ` ``) 전면 적용**:
  - MERGE INTO 쿼리 내 `ON` 조건절(`T.`{pk}` = S.`{pk}``), `UPDATE SET` 절(`T.`{col}` = S.`{col}``), `INSERT` 컬럼 목록(`(`{col1}`, `{col2}`)`), `VALUES` 절(`(S.`{col1}`, S.`{col2}`)`) 및 UNNEST SELECT Alias(`AS `{col}``)에 백틱(`` ` ``)을 전면 적용.
  - 한글 컬럼명, 공백/특수문자 포함 컬럼 및 BigQuery 예약어(`order`, `status`, `date`, `group` 등) 컬럼과의 구문 충돌 완벽 방지.
  - JSONPath 경로 내 큰따옴표 이스케이프(`$.\"{col}\"`) 적용으로 유니코드 및 특수 키 파싱 안정성 확보.

### v0.4.16 (2026-09-01)
- **`ProgressTracker` 로그 ID 기반 예외 유형별 집계 및 `logging_messages.yml` 동적 연동 요약 리포트(`log_summary`) 지원**:
  - `self.error_counts_dict: dict[str, int]` 및 에러 누적 기록 메서드 `record_error(error_type_str, count_int=1)` 추가.
  - 다단계 처리 및 복합 프로세스 간 에러 통계 병합용 `merge_error_counts(other_error_counts_dict)` 추가.
  - `update(..., error_type_str="")` 파라미터 지원으로 실패 카운트와 에러 유형 동시 갱신 지원.
  - **하드코딩 배제 및 `logging_messages.yml` 동적 연동**: 소스코드 내 하드코딩 사전 없이 `ConfigLoader`를 통해 `agent_common/config/logging_messages.yml` 및 `config/logging_messages.yml`의 메시지 템플릿을 동적으로 탐색하고 정제하여 요약 리포트에 `* 로그ID (한글설명): N 건` 형식으로 자동 출력.
  - 세 메인 프로그램(`ecs_to_gcs.py`, `ecs_to_bigquery.py`, `ecs_to_gcsbigquery_merge.py`)의 런타임 로그 ID 기반 예외 통계 연동.

### v0.4.15 (2026-09-01)
- **`ProjectLogger` 프로그램별 차등 로깅 레벨(`logging.level.<app_name>`) 지원**:
  - `config.yml`의 `logging.level`에 프로그램별 레벨 딕셔너리(`ecs_to_gcs`, `ecs_to_bigquery`, `ecs_to_gcsbigquery_merge` 등) 설정 시, 실행되는 애플리케이션 명칭(`app_name` 또는 `sys.argv[0]`)을 매칭하여 차등 로깅 레벨 적용.
  - 기존 단일 문자열(`logging.level: "INFO"`) 설정과의 완벽한 하위 호환성 유지.
  - 프로그램별 명시적 `app_name` 전달을 통해 임포트 또는 스크립트 실행 환경에서도 신뢰성 높은 로깅 레벨 바인딩 보장.

### v0.4.14 (2026-08-31)
- **`ReadOnlyConfig` 및 `ConfigLoader` 타입 접미사 자동 형 변환 및 타입 보증(Type Guarantee & Coercion)**:
  - `_int`: `int()` 자동 정수 변환 보증
  - `_float`: `float()` 자동 실수 변환 보증
  - `_bool`: `bool()` 자동 불리언 변환 보증 (`"true"`, `"false"`, `1`, `0` 등 문자열/숫자 완벽 대응)
  - `_str`: `str().strip()` 자동 문자열 변환 및 공백 제거
  - `_list` / `_dict`: 리스트/딕셔너리(ReadOnlyConfig) 타입 보증
  - 호출부에서 불필요한 방어적 `int(config.xxx_int)` 형변환 코드 제거 가능하도록 보증 체계 확립.

### v0.4.13 (2026-08-30)
- **`ReadOnlyConfig` 및 `ConfigLoader`의 `_str` 타입 접미사 설정값 자동 `.strip()` 처리**:
  - `ReadOnlyConfig.__getattr__`, `ConfigLoader.setting()`, `ConfigLoader.require_setting()`에서 `_str` 접미사로 끝나는 설정 키 조회 시 문자열 값에 대해 자동으로 `.strip()` 처리를 적용하여 호출부의 중복 `str().strip()` 코드 제거 및 안정성 강화.
  - 관련 docstring 및 타입 가이드 보강.

### v0.4.12 (2026-08-30)
- **`ConfigLoader` 미사용 함수, 불필요한 중간 변수 및 미사용 임포트 정리**:
  - `ConfigLoader` 내 단순 위임 껍데기 함수인 `configure()` 및 중복 게터 `config_dir_get()` 제거 (파이썬 표준 `@property def config_dir`로 일원화).
  - 모듈 레벨의 불필요한 중간 변수 `_default_loader` 및 미사용 상수(`CONFIG_DIR`, `ROOT`, `PACKAGE_DIR`)를 제거하고, `config = ReadOnlyConfig(ConfigLoader())`로 직결 단일화.
  - 모듈 상단의 미사용 임포트(`time`, `lru_cache`, `Dict`) 정리.
  - 설정 파일 자가 치유 및 자동 생성용 `ensure_config_file()`은 인프라 유지 관리용으로 온전히 보존.

### v0.4.11 (2026-08-30)
- **`ReadOnlyConfig` 및 전역 `config` 바인딩 구조 정비 (AGENTS.md 1.4.6 준수)**:
  - `ConfigLoader` 내의 불필요한 위임 껍데기(Pass-through) 프로퍼티(`@property def config`)를 완전히 제거.
  - `ReadOnlyConfig`가 딕셔너리(`dict`)뿐만 아니라 `ConfigLoader` 인스턴스를 직접 수용하도록 확장하여, 스키마 등록(`register_schema`)이나 동적 설정 갱신 시 실시간 최신 설정을 점 표기법(`config.ecs.base_folder`)으로 안전하게 조회할 수 있도록 개선.
  - 전역 `config` 객체를 `ReadOnlyConfig(_default_loader)`로 직결하여 불필요한 호출 레이어를 해소.

### v0.4.10 (2026-08-28)
- **`ReadOnlyConfig` 불필요한 `get()` 메서드 제거 및 점 표기법(Dot-notation) 접근 일원화**:
  - `ReadOnlyConfig`에서 딕셔너리 폴백용 `get()` 메서드를 제거하고, AGENTS.md 1.4.2 및 Fail-Fast 정책에 따라 `config.section.key` 점 표기법 및 인덱싱(`config['section']`)으로 설정 접근 체계를 단일화.

### v0.4.9 (2026-08-26)
- **외래어 '파싱'의 우리말 '해석' 순화 및 용어 표준화**:
  - `tool_parser.py`, `error_handler.py`, `config_loader.py`, `logging_messages.yml`, `README.md`의 주석, 독스트링 및 예외/로그 메시지에서 외래어 '파싱'을 직관적인 우리말 표준 용어인 '해석'으로 변경.

### v0.4.8 (2026-08-26)
- **`ProgressTracker` 대상 건수 0건(`total_items_int=0`) 지원 및 `ZeroDivisionError` 방지 구조 개선**:
  - `ProgressTracker.__init__`에서 `total_items_int`가 0일 때 강제로 1로 보정하던 로직을 `max(0, total_items_int)`로 변경하여 요약 리포트(`log_summary`)에서 실제 대상 건수 `0 건`이 정확하게 표시되도록 수정.
  - 진행률 백분율 계산 시 `max(1, self.total_items_int)`를 제수로 사용하여 0건 대상 처리 시 발생할 수 있는 `ZeroDivisionError`를 원천 방지.

### v0.4.7 (2026-08-25)
- **`fastapi` 의존성 선택적(Optional) 처리 및 패키지 경량화**:
  - `error_handler.py` 내 `fastapi` 모듈 임포트를 `try-except` 기반 동적 로딩으로 전환하여 `fastapi` 미설치 환경에서도 `agent_common`을 안전하게 임포트 및 활용할 수 있도록 개선.
  - `pyproject.toml` 및 휠 메타데이터(`Requires-Dist`)의 필수 의존성에서 `fastapi`를 제외하여 오프라인 환경(`whls`)에서의 의존성 충돌 해소.

### v0.4.6 (2026-08-24)
- **`ProjectLogger.configure` 로그 디렉터리 및 핸들러 생성 예외 처리 강화**:
  - `log_file_path.parent.mkdir` 및 `logging.FileHandler` 초기화 블록에 `try-except` 예외 처리(`PermissionError`, `OSError`, `Exception`) 추가.
  - 로그 저장 디렉터리 권한 부족이나 생성 실패 시 프로세스가 비정상 종료(Crash)되지 않고 경고 메시지 출력 후 안전하게 콘솔 출력(StreamHandler)으로 폴백하도록 안정성 개선.
  - 내부 변수명 Rule 1.6.1 타입 접미사(`today_dt`, `dynamic_log_path`, `log_file_path`, `file_handler_obj`) 적용.

### v0.4.5 (2026-08-24)
- **`llmpool.yml` Groq Qwen 3.6 27B 및 GPT-OSS-20B 모델 프로필 신설**:
  - `groq_qwen_36_27b`: Qwen 3.6 27B 추론 모델 (`qwen/qwen3.6-27b`) 프로필 추가 (다국어/코딩 추론 및 질의응답 지원).
  - `groq_gpt_oss_20b`: GPT-OSS-20B 경량화 모델 (`openai/gpt-oss-20b`) 프로필 추가.

### v0.4.4 (2026-08-24)
- **AGENTS.md 1.4.1조 준수 (메서드 내 중첩 함수 제거 및 독립 private 메서드 분리)**:
  - `ProjectLogger.get_log_msg`: 내부 함수 `_search_in_level`을 클래스 독립 private 메서드 `_search_template_in_level`로 분리 및 한글 docstring, 타입 접미사 보강.
  - `ToolParser.eval`: 내부 함수 `_replace_placeholder`를 클래스 독립 private 메서드 `_resolve_placeholder_token`으로 분리.

### v0.4.3 (2026-08-24)
- **`llmpool.yml` Groq 모델 프로필 정리 및 `openai/gpt-oss-120b` 표준화**:
  - 미지원 레거시 모델 프로필(`groq_llama33_70b`, `groq_qwen_coder_32b`) 전면 제거.
  - `groq_gpt_oss` (`openai/gpt-oss-120b`) 모델을 AGENTS.md 룰 감독관 및 주력 오픈소스 모델로 단일 표준화.
- **`ProjectLogger.get_log_msg` 파라미터 충돌 방지 및 타입 접미사 표준화**:
  - `code` 파라미터명을 `msg_code_str`로 변경하여 `kwargs`에 `code=...` 인자 전달 시 발생하는 `TypeError` 원천 방지 및 Rule 1.6.1 준수.

### v0.4.2 (2026-08-24)
- **`llmpool.yml` Groq 모델 풀 연동 기반 구축**:
  - `groq_gpt_oss` 모델 프로필 추가 및 Groq OpenAI 호환 엔드포인트 연동.

### v0.4.1 (2026-08-21)
- **`BigQueryClient.load_table_from_json_data` 변수 정의 누락 보정**:
  - `table_target` 변수 미정의 결함을 수정하여 `self.table_obj` 또는 `table_ref`를 안전하게 참조하도록 보강.
- **클래스 전반의 로거 인스턴스 명칭 표준화**:
  - `self.logger_obj`를 `self.logger`로 일괄 통일.

### v0.4.0 (2026-08-21)
- **`agent_common.tool_parser.ToolParser` 및 이원화된 Tool 디렉터리 계층 아키텍처 신설 (Major Update)**:
  - `ToolParser` 클래스 신설: 이원화된 도구 계층(1순위: 내장 `agent_common/tool`, 2순위: 로컬 `medallion/tool`) 동적 로드 및 `{ }` 템플릿 구문 치환/평가 엔진 제공.
  - `agent_common/tool/date/` 내장 범용 도구 신설: `DateTimeUtils`, `get_now_compact` (14자리 일시), `get_today` (8자리 일자), `get_now_formatted` (포맷팅 일시).
  - 시스템 표준 네임스페이스 `sys` 확장 및 공통 스키마(`agent_common/schemas/sys.json`) 탑재: `{sys.now_compact}`, `{sys.timestamp_compact}` (14자리 일시) 기본 제공.
  - `agent_common` 최상위 패키지에서 `ToolParser` 노출 (`from agent_common import ToolParser`).

### v0.3.80 (2026-08-21)
- **소스 코드 헤더 설계자(김유상) 및 설계자 소속(경포씨엔씨) 명칭 정정**:
  - 모든 모듈 파일 헤더 내 저작권 및 설계자 정보 명칭을 '김유상/경포씨엔씨'로 통일 및 정정.

### v0.3.79 (2026-08-21)
- **`BigQueryClient` 범용 SELECT 쿼리 메서드(`query`) 신설**:
  - 임의의 SQL 쿼리를 실행하여 결과 행들을 `list[dict[str, Any]]` 형태로 반환하는 범용 `query()` 메서드 추가 (공통 코드 테이블 `TCTBICM02` 실시간 조회 등 지원).

### v0.3.78 (2026-08-20)
- **`BigQueryClient` 입력 데이터(JSON dict/list) 정규화 및 분기 로직 간소화**:
  - `load_table_from_json_data`, `insert_rows_json_data`, `merge_table_from_json_data` 내 중복 `if/elif` 분기 처리를 한 줄 조건식 정규화로 개선하여 가독성 향상.

### v0.3.77 (2026-08-20)
- **BigQuery 적재 시 삭제 상태 자산(`asstStusCd == '09'`) 능동적 필터링 및 로그 템플릿 추가**:
  - `logging_messages.yml` 내 `bq_deleted_asst_stus_skipped`, `bq_all_rows_deleted_asst_stus_skipped` 경고 템플릿 등록.
  - `EcsToBigQueryTransferManager._filter_payload_by_asst_stus` 구현: GCS 실체 검증 이전에 자산상태코드가 `'09'`인 행을 능동적으로 선제 필터링하여 BigQuery 적재 대상에서 제외.

### v0.3.76 (2026-08-20)
- **`ProgressTracker` 유틸리티 및 배치 실시간 진행률/최종 요약 리포트 시스템 구축**:
  - `ProgressTracker` 클래스 신설: 실시간 진행률(`[N/Total] (P%)`, 성공/실패/제외 카운트, 경과시간, 전송량) 추적.
  - 진행률 레벨 차등 출력: 일반 진행률은 `INFO` 레벨로 출력하되, `config.yml`의 `logging.progress_interval_percent`(기본값: `10%`) 배수 마일스톤 및 완료 시점은 `WARNING` 레벨로 승격 출력하여 `WARNING` 운영 모드에서도 모니터링 보장.
  - 최종 결과 요약(Summary Report) 블록을 `WARNING` 레벨로 출력.
  - 세 메인 프로그램(`ecs_to_gcs.py`, `ecs_to_bigquery.py`, `ecs_to_gcsbigquery_merge.py`)에 `ProgressTracker` 및 Summary Report 전면 연동.

### v0.3.75 (2026-08-20)
- **로그 파일 생성 활성화/비활성화 제어 옵션(`logging.file_logging` 및 CLI `--file-log`/`--no-file-log`) 지원**:
  - `config.yml` 내 `logging.file_logging` (기본값: `true`) 설정 항목 추가.
  - `ProjectLogger.configure`에 `file_logging` 파라미터를 추가하여 파일 로깅 활성화 여부를 동적으로 제어(비활성화 시 FileHandler 생성을 건너뛰고 콘솔 출력만 유지).
  - 세 메인 프로그램(`ecs_to_gcs.py`, `ecs_to_bigquery.py`, `ecs_to_gcsbigquery_merge.py`)의 CLI 옵션에 `--file-log` 및 `--no-file-log` 플래그 추가.

### v0.3.74 (2026-08-20)
- **BigQuery TIMESTAMP 타임존 오프셋 설정(`bigquery.timezone_offset`) 및 포맷팅 지원**:
  - `config.yml` 내 `bigquery.timezone_offset` (기본값: `+09:00`) 설정 항목 추가 및 `BigQueryClient`에 바인딩.
  - `BigQueryClient.format_timestamp`에서 원천 데이터에 타임존이 없을 경우 `config.yml`의 `timezone_offset`을 자동 부여하고, 기존 타임존 오프셋(`Z`, `+09:00` 등)은 그대로 보존하도록 개선.
  - `DateTimeUtils.FORMAT_DATETIME_STD` 기본 포맷을 `%Y-%m-%d %H:%M:%S+09:00`로 일원화하여 `{sys.now}` 및 시스템 생성 타임스탬프에 KST 타임존 오프셋 명시.

### v0.3.73 (2026-08-20)
- **`ProjectLogger` 실제 호출 원천 위치(파일명, 라인 번호, 함수명) 추적 개선**:
  - `ProjectLogger` 래퍼 메서드(`info`, `warning`, `error`, `critical`, `debug`, `exception`, `log_msg`)에 `stacklevel=2`를 적용하여 어댑터 내부 위치(`logger.py:245 warning()`) 대신 실제 호출한 원천 소스코드 위치(예: `rule_evaluator.py:309 resolve_folder_and_post_dict()`, `ecs_to_bigquery.py:238 main()`)를 정확히 출력하도록 개선.

### v0.3.72 (2026-08-19)
- **BigQuery 적재 모드 및 안전 확인 로그 메시지 템플릿 추가**:
  - `logging_messages.yml` 내 `table_truncate_warning` (`WARNING.db`), `operation_cancelled_by_user` (`INFO.lifecycle`) 메시지 템플릿 등록.

### v0.3.71 (2026-08-19)
- **`BigQueryClient.insert_json_data` 단순 포워딩 래퍼 메서드 제거**:
  - `load_table_from_json_data`를 단순히 호출만 하는 불필요한 전달(pass-through) 메서드인 `insert_json_data`를 제거하여 명시적인 API 호출(`load_table_from_json_data`, `insert_rows_json_data`, `merge_table_from_json_data`)로 일원화.

### v0.3.70 (2026-08-18)
- **`ConfigLoader.require_setting` 하드코딩 제거 및 파일 로드 격리**:
  - `config_file` 인자 기본값을 `None`으로 변경하여 하드코딩 제거.
  - 특정 파일 경로 지정 시 `config.yml` 및 `get_settings()` 전역 캐시와 완전히 격리하여 독립 로드 및 검증 수행.

### v0.3.69 (2026-08-18)
- **`ConfigLoader.require_setting` 다중 경로 및 도메인 룰 파일 탐색 확장**:
  - `require_setting`이 `config/` 디렉터리뿐만 아니라 `medallion/bronze/facts_rules.yml`, `medallion/gold/table_rules.yml` 등 프로젝트 내 임의의 상대/절대 파일 경로를 직접 지정받아 검증할 수 있도록 지원.
  - `load_facts_rules`, `load_table_rules`, `load_column_codes`의 중복 파일 검증 로직을 `require_setting`으로 일원화(SRP/DRY 준수).

### v0.3.68 (2026-08-18)
- **`GcsClient` 로거 및 예외 처리 수정**:
  - `GcsClient` 초기화 시 `self.logger` 속성을 표준 바인딩하여 `AttributeError` 원천 차단.
  - 버킷 연결 실패 시 `ConnectionError` 예외 메시지 포맷팅을 명확하게 수정.

### v0.3.67 (2026-08-17)
- **모듈 레벨 레거시 함수 별칭 제거 및 `ConfigLoader` 객체지향 캡슐화 일원화**:
  - `config_loader.py` 내의 모듈 레벨 전역 함수 별칭(`configure`, `get_settings`, `setting`, `require_setting`, `register_schema`, `ensure_config_file`, `project_path`, `config_dir_get`, `config_dir_set`)을 전면 제거.
  - `agent_common/__init__.py`의 `__all__`을 `ConfigLoader`, `ReadOnlyConfig`, `config`, `clients`, `DateTimeUtils`, `llm` 핵심 객체로 정돈.
  - 전역 스키마 등록 및 자가 치유를 `ConfigLoader().register_schema()` / `ConfigLoader().ensure_config_file()` 인스턴스 메서드로 일원화하여 Rule 1.5 준수.

### v0.3.66 (2026-08-17)
- **`schemas/` 디렉터리 내 YAML 설정 자동 탐색 및 병합 지원**:
  - `ConfigLoader.get_settings`에서 `schemas/**/*.yml` 파일도 자동으로 탐색하여 `config` 계층 구조에 병합하도록 확장.
  - 빅쿼리 테이블 룰 및 코드 정의 파일(`table_column_code.yml`, `table_rules.yml`, `TCTBIIG01_constraint.sql`, `TCTBIIG01_schema.json`)의 `schemas/bigquery/` 배치 지원.

### v0.3.65 (2026-08-17)
- **`db_load_*` 배치/단건 적재 재시도 및 실패 로깅 템플릿 범용화**:
  - `db_load_retry`, `db_load_max_retries_exceeded_fallback`, `db_load_max_retries_exceeded`, `db_streaming_fallback_failed` 템플릿을 `agent_common`으로 이관.
  - 프로젝트 루트의 `bq_load_*` 레거시 키 5종 정리 완료.

### v0.3.64 (2026-08-17)
- **`db_merge_load_failed` 및 `storage_client_init_failed` 범용 통합**:
  - `bq_merge_load_failed`를 `db_merge_load_failed`(`{service_name} 병합(MERGE) 적재 최종 실패: ...`)로 대체하여 `agent_common`에 등록.
  - `gcs_client_init_failed`를 `storage_client_init_failed`(`{storage_type} 클라이언트 초기화 실패: ...`)로 일원화.

### v0.3.63 (2026-08-17)
- **DB 로깅 템플릿 내 `{service_name}` 플레이스홀더 표준화 및 호출부 동기화**:
  - `agent_common/config/logging_messages.yml`의 `db` 관련 모든 메시지(`db_inline_merge_*`, `db_bulk_load_*`, `db_load_*`, `db_transfer_skipped`)에 다중 DB 식별용 `{service_name}` 플레이스홀더 적용.
  - `clients.py` 및 메인 파이프라인에서 `service_name="BigQuery"` 전달 구조로 완전 동기화.

### v0.3.62 (2026-08-17)
- **`db_bulk_load_*` 대량 적재 범용 로깅 템플릿 추가 및 `agent_common` 승격**:
  - `db_bulk_load_started`, `db_bulk_load_completed`, `db_bulk_streaming_fallback_success`, `db_bulk_load_retry`, `db_bulk_load_max_retries_exceeded_fallback`, `db_bulk_load_skipped_no_data`, `db_bulk_load_failed`, `db_bulk_streaming_fallback_failed` 템플릿을 `agent_common`으로 이관.
  - `app/ecs_to_bigquery.py` 및 `app/ecs_to_gcsbigquery_merge.py`의 벌크 적재 로깅 호출을 범용 표준 키로 일괄 변경.

### v0.3.61 (2026-08-17)
- **`client_initialized` 범용 초기화 로깅 템플릿 통합 및 `agent_common` 승격**:
  - `bq_client_initialized`, `bq_gcs_client_initialized`를 범용 템플릿인 `client_initialized`(`{client_name} 클라이언트가 성공적으로 초기화되었습니다.`)로 단일 통합.
  - `app/ecs_to_gcsbigquery_merge.py` 및 `app/ecs_to_bigquery.py`의 클라이언트 초기화 로깅을 `client_initialized`로 통일.

### v0.3.60 (2026-08-17)
- **`db_transfer_skipped` 범용 로깅 메시지 템플릿 추가 및 도메인 메시지 이관**:
  - `agent_common/config/logging_messages.yml`의 `INFO.db` 섹션에 `db_transfer_skipped` 템플릿 등록.
  - `app/ecs_to_bigquery.py`의 사전 적재 건너뜀 로깅을 `db_transfer_skipped`로 통일.

### v0.3.59 (2026-08-17)
- **`clients.py` AGENTS.md 1.8 타입 접미사(Type-Suffix) 및 2. Docstring 규격 전면 일치화**:
  - `merge_table_from_json_data`의 파라미터 및 내부 모든 변수(`_str`, `_int`, `_list`, `_dict`, `_set`, `_float`)에 엄격한 타입 접미사 적용.
  - `:return: None`, `:raises ValueError`, `:raises RuntimeError` 등 한글 표준 독스트링 규격 보강.

### v0.3.58 (2026-08-17)
- **DB 테이블 병합 예외 로깅 키 명확화 (`merge_failed` ➔ `db_table_merge_failed`)**:
  - 모호했던 `merge_failed`를 데이터베이스 테이블 병합 실패임을 직관적으로 식별할 수 있도록 `db_table_merge_failed`로 수정 및 `clients.py`와 동기화.

### v0.3.57 (2026-08-17)
- **`clients.py` 내 `merge_table_from_json_data` 중복 정의 및 독스트링 오탈자 수정**:
  - 함수 교체 과정에서 잔존했던 중복 `def` 헤더 및 독스트링 따옴표 블록을 온전하게 정리.

### v0.3.56 (2026-08-17)
- **`BigQueryClient.merge_table_from_json_data` 내 도메인 컬럼/상수 하드코딩 완전 제거 (순수 범용화)**:
  - `asstStusCd`, `'09'`, `hrkOriginDocFileId`, `fileRoleCd`, `bqAmndHMS` 등 비즈니스 특정 컬럼 및 상수 하드코딩을 100% 제거.
  - Python 데이터 타입(dict/list -> JSON, int -> INT64, float -> FLOAT64, bool -> BOOL) 자동 추론 및 `column_types`, `not_matched_condition`, `post_queries` 주입 파라미터 구조로 완전 일반화.
  - 비즈니스 도메인 로직(자산 삭제 방어 및 첨부파일 연쇄 비활성화)은 `app/ecs_to_gcsbigquery_merge.py`에서 `config` 기반으로 전달하도록 리팩토링.

### v0.3.55 (2026-08-17)
- **`agent_common` 로깅 메시지 키 접두사 전면 범용화 (`db_`, `storage_`)**:
  - `bq_inline_merge_*` ➔ `db_inline_merge_*`, `ecs_folder_search_*` ➔ `folder_search_*` 등 키 이름 자체의 벤더 종속성을 제거하고 완전한 범용 표준 키로 통일.

### v0.3.54 (2026-08-17)
- **`agent_common` 공통 로깅 메시지 템플릿 범용화 및 도메인 메시지 분리**:
  - `agent_common/config/logging_messages.yml` 내의 메시지를 특정 도메인에 종속되지 않는 범용적 표준 표현으로 전면 일반화(Generalization).
  - 프로젝트 도메인 고유 메시지는 프로젝트 루트 `config/logging_messages.yml`로 명확히 분리 및 계층화.

### v0.3.53 (2026-08-17)
- **`logging_messages.yml` 전수 조사 및 누락 템플릿 일괄 등록**:
  - `BigQueryClient.merge_table_from_json_data` (`bq_inline_merge_started`, `bq_inline_merge_chunk_completed`, `bq_cascade_attach_deleted`, `bq_inline_merge_all_completed`, `merge_failed`) 등 BigQuery MERGE 관련 메시지 등록.
  - ECS 폴더 탐색, 파일 추출, 룰/스키마 동적 로드 실패 등 전역 누락 메시지 템플릿 100% 등록 완료.

### v0.3.52 (2026-08-17)
- **`ConfigLoader._find_project_root` 내 `sys.argv[0]` 예외 명시화**:
  - 모듈 임포트 시점 특수 CLI/REPL 환경의 경로 해석 실패를 안전하게 방어하도록 `(ValueError, OSError)` 명시 및 방어 목적 주석 보강.

### v0.3.51 (2026-08-17)
- **`clients.py` 내 모든 `except` 블록 예외 로깅 `logger.exception` 전면 통일**:
  - `EcsClient`, `GcsClient`, `BigQueryClient`의 연결, 파일 전송, 메타데이터 조회, 테이블 적재 실패 등 모든 `except` 블록에서 스택 트레이스 보존을 위해 `logger.exception`으로 전면 통일.

### v0.3.50 (2026-08-17)
- **`ConfigLoader` 예외 블록 `self.logger.exception` 적용**:
  - `ensure_config_file` 내 파일 생성 및 자동 보정 실패 시, AGENTS.md 1.9.3 규칙에 따라 스택 트레이스 정보를 온전히 보존하도록 `logger.exception`으로 일원화.

### v0.3.49 (2026-08-16)
- **`logging_messages.yml` 내 `config` 파일 자동생성/자동보정 메시지 템플릿 추가**:
  - `config_file_auto_created` (INFO): 설정 파일 미존재 시 기본 템플릿 신규 자동 생성 완료 안내 메시지 등록.
  - `config_file_auto_repaired` (INFO): 설정 파일 내 누락 키 자동 보정(Self-healing) 완료 안내 메시지 등록.
  - `config_auto_create_failed` (WARNING): 설정 파일 자동 생성 실패 경고 메시지 등록.
  - `config_auto_repair_failed` (WARNING): 설정 파일 자동 보정 실패 경고 메시지 등록.

### v0.3.48 (2026-08-16)
- **`ConfigLoader` 내 시간 생성 로직 `DateTimeUtils.get_now_formatted`로 통합**:
  - `ensure_config_file`에서 헤더 및 자동 복구 주석 생성 시 사용하던 `time.strftime` 하드코딩을 `DateTimeUtils.get_now_formatted()`로 교체하여 전사 일시 규격 100% 일원화.

### v0.3.47 (2026-08-16)
- **`DateTimeUtils` 전사 공통 날짜/시간 표준 규격 유틸리티 추가**:
  - `get_today_yyyymmdd()`: `YYYYMMDD` (8자리) 당일자 반환.
  - `get_now_formatted()`: `YYYY-MM-DD HH:MM:SS` 표준 일시 반환.
  - `get_now_compact()`: `YYYYMMDDHHMMSS` (14자리) 압축 일시 반환.

### v0.3.46 (2026-08-16)
- **`BigQueryClient.format_timestamp` BigQuery 표준 타임스탬프 포맷팅 공통 메서드 추가**:
  - 다양한 형태의 원천 날짜/시간 문자열(`YYYYMMDD`, `YYYYMMDDHHMMSS`, ISO8601 등)을 BigQuery 표준 `YYYY-MM-DD HH:MM:SS` 문자열로 안전하게 변환하는 공통 메서드 제공.

### v0.3.45 (2026-08-16)
- **`BigQueryClient.merge_table_from_json_data` 삭제 건(09) INSERT 방어 및 하위 첨부파일 연쇄 비활성화(Cascading Update) 기능 추가**:
  - 기존 데이터 미존재 시 `asstStusCd == '09'`인 데이터의 불필요한 신규 INSERT 방어 (`WHEN NOT MATCHED AND S.asstStusCd != '09'`).
  - 삭제된 상위 원문(`fileRoleCd == '01'` & `asstStusCd == '09'`)의 ID를 추출하여 종속된 하위 첨부파일(`hrkOriginDocFileId IN UNNEST(@parent_ids)`)을 함께 `09` 및 현재시간 `bqAmndHMS`로 일괄 갱신.

### v0.3.44 (2026-08-16)
- **`clients.py` 상단 누락된 `time`, `json`, `List`, `Optional` import 보강**:
  - `merge_table_from_json_data` 메서드에서 참조하는 표준 라이브러리 및 타입 힌트 임포트 누락 수정.

### v0.3.43 (2026-08-16)
- **`BigQueryClient.merge_table_from_json_data` 범용 MERGE INTO (Upsert) 메서드 추가**:
  - 임시 테이블 생성 권한(`CREATE TABLE`) 없이 DML 권한만으로 작동하는 `UNNEST(JSON_QUERY_ARRAY(@json_payload))` 기반 인라인 MERGE 로직을 `BigQueryClient` 공용 라이브러리로 이관.
  - PK 매칭(`pk_key`), 최초 생성일시 보존(`preserve_columns`), 청크 분할(`chunk_size`) 기능 지원.

### v0.3.42 (2026-08-16)
- **`require_setting` 및 `ConfigLoader` 전체 메서드 파라미터 docstring(`:param`, `:return`) 복원 및 보강**:
  - `require_setting`, `setting`, `project_path`, `_load_yaml_mapping`, `_deep_merge` 등 모든 클래스 메서드에 AGENTS.md 규칙 2.3에 따른 상세 파라미터 및 반환값 설명을 한국어 docstring으로 완벽 복원.

### v0.3.41 (2026-08-16)
- **`ensure_config_file` 누락 키 자동 추가 주석을 인라인(Inline) 형태로 간결화**:
  - 누락 키 자동 보정 시 파일 상단에 큰 주석 블록을 만드는 대신, 자동 추가된 각 키 라인 끝에 ` # [자동 추가: YYYY-MM-DD HH:MM:SS]` 인라인 주석을 부착하여 번잡함 제거 및 가독성 극대화.
  - `default_agent_common.yml`의 `templates.config_repair_inline_comment` 템플릿 사용.

### v0.3.40 (2026-08-16)
- **`ensure_config_file` 누락 키 자동 보정 시 상단 보정 이력 안내 주석(REPAIRED NOTICE) 블록 추가**:
  - 기존 설정 파일에 누락된 키가 발견되어 자동 보정될 때, 자동으로 추가된 설정 항목명(`repaired_keys`) 및 보정일시를 상단 주석 헤더로 기록하도록 개선.
  - 보정 안내 문구 템플릿(`templates.config_repair_header`)을 `default_agent_common.yml`에 분리하여 No Hardcoding 규칙 1.1 준수.

### v0.3.39 (2026-08-16)
- **`default_agent_common.yml` 내 `templates.config_notice_header` 템플릿 분리 (No Hardcoding 규칙 1.1 준수)**:
  - 소스 코드 내 하드코딩되어 있던 안내 주석 텍스트를 `agent_common/config/default_agent_common.yml`의 `templates.config_notice_header`로 완전히 분리.
  - `ConfigLoader.ensure_config_file`에서 해당 템플릿 설정을 동적으로 로드하여 포매팅하도록 리팩토링.

### v0.3.38 (2026-08-16)
- **`ensure_config_file` 자동 생성 시 상단 안내 주석(NOTICE) 블록 추가**:
  - `config.yml` 파일이 존재하지 않아 자동 생성될 때 최상단에 사람이 쉽게 인지할 수 있는 안내 문구(자동 생성 목적, 접속 정보 수정 또는 기존 파일 대체 안내, 생성일시)를 헤더 주석으로 기록하도록 개선.

### v0.3.37 (2026-08-16)
- **도메인별 설정 스키마 등록(`register_schema`) 및 자가 치유(`ensure_config_file`) 지원**:
  - 개별 프로그램에서 요구하는 기본 설정 스키마를 동적으로 등록(`register_schema`)하여 공통 설정과 결합할 수 있도록 지원.
  - `config.yml` 파일이 없으면 기본 템플릿으로 자동 생성하고, 기존 파일에 누락된 키가 있으면 기본값으로 자동 보정(Auto-repair)하는 `ensure_config_file` 함수 제공.
  - 설정 키의 무결성을 보장하여 애플리케이션 전반에서 `.get()` 방어 코드를 배제하고 순수 점 표기법(`config.xxx.yyy`)만으로 안전하게 접근할 수 있도록 환경 제공.

### v0.3.36 (2026-08-15)
- **점 표기법(Dot-notation) 기반 읽기 전용 설정 객체 `ReadOnlyConfig` 및 `config` 싱글톤 제공**:
  - `ReadOnlyConfig` 클래스를 추가하여 `config.ecs.endpoint_url`, `config.transfer.max_workers` 형태로 YAML 설정 계층에 직접 속성(Attribute)으로 접근할 수 있도록 지원.
  - 런타임에 설정값이 임의로 변경되지 않도록 불변(Read-Only) 방어 로직 (`__setattr__`, `__setitem__` 예외 발생) 적용.
  - `agent_common` 및 `agent_common.config_loader`에서 전역 `config` 객체를 직접 임포트하여 클래스 `__init__`의 불필요한 멤버 변수 바인딩 없이 코드 어디서든 즉시 사용할 수 있도록 개선.


### v0.3.35 (2026-08-15)
- **`BigQueryClient.load_table_from_json_data` 내 `write_disposition` 파라미터 지원 추가**:
  - `write_disposition` 매개변수를 추가하여 BigQuery 배치 적재 시 `WRITE_TRUNCATE` (전체 덮어쓰기) 또는 `WRITE_APPEND` (추가 적재) 옵션을 동적으로 적용할 수 있도록 확장.

### v0.3.34 (2026-08-14)
- **`ProjectLogger.configure` 동적 `{app_name}` 치환 및 ISO 8601 `T` 구분자 년월일시분초(`%Y%m%dT%H%M%S`) 포맷 지원**:
  - `ProjectLogger.configure`에 `app_name` 매개변수를 추가하고 지정되지 않은 경우 `sys.argv[0]`의 파이썬 스크립트명(stem, 예: `ecs_to_gcs`, `ecs_to_bigquery`)을 기본 프로그램명으로 자동 사용하도록 구현.
  - 로그 파일명 포맷의 `{app_name}` 템플릿 치환 지원.
  - `config.yml` 내 `out_file` 및 `debug_file` 경로 설정의 날짜/시간 포맷을 ISO 8601 `T` 구분자 기반 년월일시분초(`%Y%m%dT%H%M%S`)로 변경하여 단어 공백과의 경계 명확화 및 가독성 향상.


### v0.3.33 (2026-08-13)
- **`ProjectLogger.configure` 로그 레벨 조건별 저장 경로 (`out_file` / `debug_file`) 및 년/월/일 폴더 분리 로직 반영**:
  - `logging.level` 설정이 `ERROR` 이상일 경우 `out_file` (`logs/link/out/%Y/%m/%d/out.log`) 경로에 저장.
  - `logging.level` 설정이 `WARNING` 이하일 경우 `debug_file` (`logs/link/debug/%Y/%m/%d/debug.log`) 경로에 저장.
  - `today.strftime(...)`을 이용해 년/월/일(`%Y/%m/%d`) 디렉터리가 동적으로 자동 생성되도록 구현.

### v0.3.32 (2026-08-12)
- **`logging_messages.yml` 내 `load_table_from_json_failed` 예시 주석 추가**:
  - `ERROR.db.load_table_from_json_failed` 템플릿 항목 상단에 사용법 예시 코드 주석 추가.

### v0.3.31 (2026-08-12)
- **BigQueryClient.load_table_from_json_data 예외 발생 시 상세 Traceback 로깅 추가**:
  - `load_table_from_json_data`의 `except Exception` 블록에 `self.logger.exception` 호출을 추가하여 배치 적재 실패 시 try: 블록 내부의 상세 예외 및 Traceback 정보가 로그에 출력되도록 개선.
  - `logging_messages.yml` 내 `load_table_from_json_failed` 메시지 템플릿 추가.

### v0.3.30 (2026-08-12)
- **BigQueryClient 적재 메서드 명시적 분리 (load_table_from_json_data / insert_rows_json_data)**:
  - load_table_from_json 전용 적재 메서드(load_table_from_json_data)와 insert_rows_json 전용 적재 메서드(insert_rows_json_data)로 개별 분리하여 명확한 적재 방식 선택 지원.

### v0.3.29 (2026-08-12)
- **로그 멀티라인(Multi-line) 포매팅 전환 및 단일행 출력 제약 해제**:
  - 현대적 로그 수집기의 다중 행 처리 지원에 맞춰 SingleLineFlattenFormatter에서 강제 단일행 평탄화(flattening)를 제거하고 Multi-line Traceback 및 로그 메시지 원형 보존 지원.

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
