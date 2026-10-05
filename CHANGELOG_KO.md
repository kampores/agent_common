# 버전 변경 이력 (Changelog)

> [ KO 한국어 (CHANGELOG_KO.md) ](CHANGELOG_KO.md) | [ EN English (CHANGELOG_EN.md) ](CHANGELOG_EN.md) | [ ZH 中文 (CHANGELOG_ZH.md) ](CHANGELOG_ZH.md) | [ JA 日本語 (CHANGELOG_JA.md) ](CHANGELOG_JA.md)

### v0.4.98 (2026-10-06)

- **`GcsClient`, `BigQueryClient`의 인증과 연결 단계 분리 (규칙 1.6.4, 4.2 준수, 호환성 변경)**:
  - 생성자에서 `GcpCredentialResolver.resolve()`로 인증을 먼저 수행하고, 그 결과를 `_connect(credentials_obj)`에 넘겨 연결하도록 변경. `_connect()`의 `try` 블록에는 클라이언트 생성과 버킷·테이블 조회만 남음.
  - 호환성: 인증 단계 예외(`ImportError`, `ValueError`, `FileNotFoundError` 등)가 더 이상 `ConnectionError`로 감싸지지 않고 원래 타입 그대로 전달됨. 인증 실패를 `ConnectionError`로 잡던 코드는 수정 필요.
  - 인증 실패 로그를 클라이언트가 아닌 `GcpCredentialResolver`가 예외 발생 지점에서 한 번 기록하도록 변경. 리졸버를 단독으로 쓸 때도 같은 로그가 남으며, 클라이언트는 이를 다시 기록하지 않음. 이를 위해 리졸버에 `self.logger`를 추가하고 `_get_service_account`를 클래스 메서드에서 인스턴스 메서드로 변경 (모듈 캐시는 클래스 변수 유지).
  - 소스 코드에 한글로 적혀 있던 리졸버의 예외 문장을 로그 메시지 사전으로 이동 (4개 언어): `credential_package_missing`(`ImportError`), `credential_json_invalid`(`ValueError`), `credential_file_not_found`(`FileNotFoundError`). 예외 메시지가 로그 언어 설정을 따르며, 인증 실패 로그 ID는 `connection_failed`에서 이 세 가지로 바뀜.
  - 키 파일 미존재 메시지의 출처 표기를 `config.yml 설정값`에서 인자명 `credentials_path_str`로 변경.
  - 매뉴얼 `3.6`의 예외 처리 가이드를 4개 언어로 갱신.
- **`S3Client.transfer_to_gcs` 소요시간 로그를 결과 로그에 통합 (규칙 1.1.1, 3.2, 4.2 준수)**:
  - 파일마다 결과 로그 뒤에 따로 남기던 `elapsed_time` 로그를 제거하고, 구간별 소요시간(`details_str`)과 전송 컨텍스트(`context_info_str`)를 결과 로그 한 줄에 함께 기록. 파일 1건당 로그가 2줄에서 1줄로 감소.
  - 소스 코드에 한글로 적혀 있던 `action_name_str` 값("GCS 파일 검사", "GCS 파일 전송", "GCS 파일 전송 오류")을 삭제. 로그 언어를 `EN`, `ZH`, `JA`로 설정해도 이 부분만 한글로 출력되던 문제 해소.
  - 기존 문장 끝에 `{details_str} {context_info_str}` 슬롯을 붙인 템플릿 `transfer_completed_with_elapsed_time`, `transfer_skipped_with_elapsed_time`, `transfer_failed_with_elapsed_time` 추가 (4개 언어). `transfer_to_gcs`는 이 세 로그 ID를 사용.
  - 기존 `transfer_completed`, `transfer_skipped`, `transfer_failed` 템플릿은 변경 없음.
  - 건너뜀 로그의 `Status=Skipped` 토큰은 메시지 본문과 중복되어 삭제.
  - 전송 실패 1건당 `transfer_to_gcs`가 남기는 ERROR 로그가 2건에서 1건으로 줄어 실패 누적 건수가 그만큼 감소하고, 오류 유형별 집계에서 `elapsed_time` 대신 `transfer_failed_with_elapsed_time`이 표시됨.
  - `elapsed_time` 템플릿은 그대로 유지.
- **매뉴얼 `3.1` 보완 (규칙 4.2 준수)**:
  - 전송 파이프라인 흐름도의 건너뜀 단계 표기를 변경된 로그 구조에 맞게 수정 (한국어, 영어, 일본어).

### v0.4.97 (2026-10-05)

- **설정 파일 자동 생성·보정 대상을 클래스 단위로 선택 (규칙 1.7.5, 4.2 준수, 호환성 변경)**:
  - 신규 설정 `config_loader.config_file_auto_repair_dict`: `<클래스명>_bool` 형식의 키(예: `BigQueryClient_bool`)로 클래스별 활성화 여부를 지정하는 사전. 기본값은 전부 `false`이며, `ensure_config_file()`은 `true`인 클래스의 기본 설정만 `config.yml`에 기록.
  - 대상 클래스: `ConfigLoader`, `ProjectLogger`, `S3Client`, `GcsClient`, `GcpCredentialResolver`, `BigQueryClient`, `ProgressTracker`, `TableFormatter`, `ToolParser`, `LlmClient`. 각 클래스에 기록할 기본 설정을 담은 `DEFAULT_SCHEMA_DICT` 클래스 속성 추가.
  - 호출 프로그램이 넘긴 스키마(`register_schema()` 등록분, `default_schema` 인자)는 기존과 같이 항상 생성·보정.
  - 값은 `_bool` 접미사 규칙으로 해석(`true`/`false` 및 같은 뜻의 문자열, 그 밖의 값은 즉시 오류). 켠 키에 해당하는 클래스가 `agent_common`에 없으면 경고 로그 `config_auto_repair_unknown_class`를 남기고 건너뜀 (4개 언어 메시지 추가).
  - 호환성: 이전 버전은 `LlmClient`를 쓰지 않아도 `llm`, `llm_pool` 항목을 `config.yml`에 자동 추가했으나 이제 추가하지 않음. 필요하면 `LlmClient_bool: true`로 지정.
- **전역 스키마 등록 메서드 추가 (규칙 1.5.4 준수)**:
  - `ConfigLoader.register_schema_globally(schema_dict)`: 넘겨받은 스키마를 전역 스키마 레지스트리에 등록. `ReadOnlyConfig.register_schema()`가 세 군데에서 호출하고 있었으나 `agent_common`에 정의가 없어, 해당 분기를 타면 `AttributeError`가 나던 문제 해소.
  - `ConfigLoader.register_enabled_class_schemas_globally()`: `config_loader.config_file_auto_repair_dict`에서 `true`인 클래스의 `DEFAULT_SCHEMA_DICT`만 전역 등록. `ensure_config_file()`이 가장 먼저 호출하므로, 켠 클래스의 기본 설정은 파일 기록과 실행 중 기본값에 함께 적용.
  - 이미 등록된 호출 프로그램 스키마의 값은 클래스 기본값으로 덮어쓰지 않음.
- **LLM 기본 설정을 패키지 기본 설정 파일로 이동**:
  - `llm.py`가 임포트 시점과 `LlmClient` 생성 시점에 `register_schema()`로 전역 등록하던 동작을 제거하고, 같은 값(`llm.router_model_str`, `llm.sql_generator_model_str`, `llm.system_prompt_str`, `llm.default_purpose_str`)을 `default_agent_common.yml`에 정의. 런타임 설정값은 동일.
- **`clients.py` 모듈 스키마를 클래스별로 분리**:
  - 모듈 전역 `APP_DEFAULT_SCHEMA_DICT`를 삭제하고 `S3Client`, `GcsClient`, `GcpCredentialResolver`, `BigQueryClient`의 `DEFAULT_SCHEMA_DICT`로 분리. 공용 키 `transfer.timeout_seconds_int`는 세 클라이언트에 각각 포함.
  - 어떤 클래스도 읽지 않던 `transfer.chunk_size_int`, `bigquery.max_retries_int`는 스키마에서 삭제.
- **`logger.py` 기본 스키마의 `logging.log_file_str` 정정**:
  - 패키지 기본 설정(`default_agent_common.yml`)과 다르던 경로 템플릿을 동일한 값으로 일치. `ProjectLogger`를 켰을 때 실제 적용 중인 기본값과 다른 경로가 기록되지 않도록 함.
- **`logging.level_dict` 조회에서 접미사 없는 키 대체 탐색 제거 (규칙 1.5.3 준수, 호환성 변경)**:
  - `ProjectLogger.configure`가 로그 레벨을 찾는 순서를 `<프로그램명>_str` 키, `default` 키의 두 단계로 정리. 접미사 없는 `<프로그램명>` 키는 더 이상 인식하지 않으므로 `<프로그램명>_str`로 바꿔야 함.
- **매뉴얼 `1.6` 보완 (규칙 4.2 준수)**:
  - 4개 국어 매뉴얼에 `2.1` 절을 추가하여 클래스 단위 선택 설정, 클래스별 기록 항목, 최초 실행 시 적용 방법을 설명.

### v0.4.96 (2026-10-04)

- **언어 식별자를 ISO 639-1 언어 코드로 통일 (규칙 1.1.3, 4.2 준수, 호환성 변경)**:
  - 국가 코드 형태였던 `KR`, `JP`를 언어 코드 `KO`, `JA`로 변경. `EN`, `ZH`는 그대로 유지하여 지원 언어는 `KO`, `EN`, `ZH`, `JA`.
  - 기본 언어와 `logging.language_str` 기본값을 `KR`에서 `KO`로 변경.
  - `Localizer`에서 국가 코드 별칭(`KR`, `JP`, `CN`, `US`)과 파일 접미사 교차 탐색(`kr`↔`ko`, `jp`↔`ja`, `zh`↔`cn`)을 삭제. 인식하지 못한 값은 기존과 같이 기본 언어 `KO`로 처리되므로, 설정에 `JP`를 쓰던 경우 `JA`로 바꿔야 함.
  - 파일명 변경: `logging_messages_kr.yml` → `logging_messages_ko.yml`, `logging_messages_jp.yml` → `logging_messages_ja.yml`.
  - 문서 경로 변경: `manual/kr` → `manual/ko`, `manual/jp` → `manual/ja` (파일 접미사 `_kr.md` → `_ko.md`, `_jp.md` → `_ja.md`), `CHANGELOG_KR.md` → `CHANGELOG_KO.md`, `CHANGELOG_JP.md` → `CHANGELOG_JA.md`, `AGENTS_KR.md` → `AGENTS_KO.md`, `AGENTS_DOCS_ENV_KR.md` → `AGENTS_DOCS_ENV_KO.md`. README와 `pyproject.toml`의 링크도 함께 갱신.
- **`Localizer` 매뉴얼 신설 및 다국어 문서 보완 (규칙 4.2 준수)**:
  - 매뉴얼 `8.1 언어 코드 정규화 및 언어별 리소스 파일 탐색`(`manual/*/localizer/01_language_codes_and_resource_lookup_*.md`)을 4개 국어로 신설하고, README 주요 기능에 `8. 언어 로컬라이저` 섹션과 매뉴얼 목록 항목 추가.
  - 매뉴얼 `2.3 다국어 로그 메시지 템플릿 사전`에 4개 언어 사전 파일과 로그 언어 결정 우선순위를 반영.
- **문서의 `agent_common.utils` 표기를 실제 모듈 경로로 정정 (규칙 4.2 준수)**:
  - 존재하지 않는 `agent_common.utils` 모듈을 가리키던 README와 매뉴얼의 표기를 `agent_common.time_utils`, `agent_common.progress_tracker`, `agent_common.table_formatter`로 수정.
  - 실행 시 `ModuleNotFoundError`가 나던 예시 코드의 `from agent_common.utils import ...`를 `from agent_common import ...`로 수정.
- **언어 이동 링크의 국기 이모지를 언어 코드로 교체 (규칙 4.2 준수)**:
  - README와 CHANGELOG 상단 언어 이동 링크의 국기 이모지(일부 환경에서 `KR`, `US`, `CN`, `JP` 국가 코드로 표시됨)를 언어 코드 `KO`, `EN`, `ZH`, `JA`로 교체.
  - README 언어별 섹션 제목에서 국기 이모지를 제거하고, 이동 링크 앵커를 새 제목(`#agent_common-패키지-한국어` 등)에 맞게 갱신.

### v0.4.95 (2026-10-04)

- **`ProjectLogger.get_log_id_description` 지역 변수명 정정 (규칙 1.6.1, 1.6.2, 4.2 준수)**:
  - 타입 접미사가 없고 축약어를 쓰던 `template_val`을 `get_log_msg`와 동일한 `template_str`로 변경.
  - 동작 변경 없음.
- **SDK 지연 로딩 함수를 클라이언트 클래스 내부로 이동 (규칙 1.4.1, 4.2 준수)**:
  - 모듈 전역 함수 `_get_boto3`, `_get_gcs`, `_get_bigquery`를 각각 `S3Client`, `GcsClient`, `BigQueryClient`의 `@classmethod`로 이동.
  - 모듈 전역 캐시 변수(`_boto3_module`, `_boto_config_cls`, `_storage_module`, `_bigquery_module`, `_service_account_module`)를 각 클래스 변수로 이동하고 `global` 선언 제거.
  - 동작 변경 없음.
- **GCP 인증 해석 전담 클래스 `GcpCredentialResolver` 신설 및 공개 (규칙 1.4.1, 1.4.7, 1.6.2, 4.2 준수)**:
  - 모듈 전역 함수 `_resolve_gcp_credentials`를 삭제하고 `GcpCredentialResolver.resolve()`로 이전. 4단계 인증 우선순위는 그대로 유지.
  - `GcsClient`, `BigQueryClient`가 상속이 아닌 합성(Composition)으로 `self.credential_resolver`를 보유하여, 어느 한 클라이언트만 분리해도 다른 클라이언트에 의존하지 않도록 구성.
  - `google.oauth2.service_account` 지연 로딩을 `GcpCredentialResolver`로 일원화. `GcsClient._get_gcs()`, `BigQueryClient._get_bigquery()`는 튜플 대신 자기 모듈 하나만 반환.
  - `agent_common` 공개 API(`from agent_common import GcpCredentialResolver`)로 등록하여 GCS·BigQuery 외 GCP 서비스에서도 재사용 가능.
  - 축약 변수명 정리: `val_str`, `cred_path`, `cred_err` → `env_credentials_path_str`, `credentials_file_path`, `credentials_error`.
  - `google-auth` 미설치 시 `ImportError`가 클라이언트 `_connect`에서 `ConnectionError`로 감싸져 전달됨.
  - 매뉴얼 `3.6 GCP 서비스 계정 인증 해석기`(`06_gcp_credential_resolver_*.md`) 4개 국어 신설, README 주요 기능·사용 예시·매뉴얼 목록에 반영.
- **KST-as-UTC 타임스탬프 모드 제거 (규칙 4.2 준수, 호환성 변경)**:
  - 현지 시각 숫자를 `+00:00`으로 저장하던 KST-as-UTC 모드를 삭제. 현지 시각을 그대로 보여야 하는 경우 `DATETIME` 컬럼과 `convert_to_bigquery_datetime`을 사용.
  - 삭제된 항목: 설정 `bigquery.kst_as_utc_timestamp_bool`, 속성 `BigQueryClient.kst_as_utc_timestamp_bool`, 메서드 `BigQueryClient.validate_and_sync_table_timestamp_mode()`.
  - 삭제된 로그 메시지 키: `table_timestamp_mode_legacy_warning`, `table_timestamp_mode_mismatch`, `table_get_failed`, `table_metadata_update_failed`.
  - `convert_to_bigquery_timestamp`는 항상 결정된 타임존 오프셋(원천 명시값 → `default_tz_offset_str` → `timezone_offset_str` → 시스템 타임존)을 붙여 반환.
- **매뉴얼 `3.5` 전면 개정 및 문서 번호 정리 (규칙 4.2 준수)**:
  - 매뉴얼 파일명을 `05_bigquery_timestamp_and_tz_sync_*.md`에서 `05_bigquery_timestamp_and_datetime_conversion_*.md`로 변경하고, `TIMESTAMP`·`DATETIME` 변환 두 메서드 중심으로 4개 국어 재작성. 그동안 누락되어 있던 `convert_to_bigquery_datetime` 규격과 사용 예시 추가.
  - README 주요 기능의 `3.6 BigQuery 표준 DATETIME 변환` 항목을 `3.5`로 통합하여, 기능 번호와 매뉴얼 파일(01~06)이 1:1로 대응하도록 정리.

### v0.4.94 (2026-10-04)

- **PyPI README 언어 이동 앵커 링크 수정 (규칙 4.2 준수)**:
  - PyPI 렌더러가 HTML `<a id="...">` 태그의 `id` 속성을 제거하여 v0.4.93의 `#kr`, `#en`, `#zh`, `#jp` 링크가 동작하지 않던 문제 수정.
  - 기존 KR/EN에서 정상 동작하던 방식과 동일하게 마크다운 헤더 자동 슬러그(`#-agent_common-패키지-한국어`, `#-agent_common-package-english`, `#-agent_common-软件包-中文`, `#-agent_common-パッケージ-日本語`)로 4개 국어 링크 통일.
  - 불필요해진 `<a id>` 태그 제거.

### v0.4.93 (2026-10-04)

- **PyPI 패키지 단일 설명(Project Description) 지원을 위한 4개 국어 통합 README 구축 (규칙 4.2 준수)**:
  - PyPI 웹사이트의 단일 README 렌더링 특성에 맞추어 한국어(KR), 영어(EN), 중국어(ZH), 일본어(JP) 4개 국어 문서를 `README.md` 단일 파일로 완전 통합 (순서: `kr` -> `en` -> `zh` -> `jp`).
  - 상단 4개 국어 다이렉트 앵커 링크(`#kr`, `#en`, `#zh`, `#jp`) 및 GitHub 저장소/PyPI 완벽 호환 절대 URL 매뉴얼 링크 체계 구축.
  - 중복되는 `README_*.md` 분할 파일 완전 정리.
- **`pyproject.toml` 다국어 프로젝트 링크(`project.urls`) 4개 국어 확대 등록**:
  - PyPI 사이드바 링크에 한국어·영어 외 중국어(ZH) 및 일본어(JP) 변경 이력(`Changelog`) 및 상세 매뉴얼(`Manual`) 링크 공식 등록.

### v0.4.92 (2026-10-04)

- **언어 로컬라이징(Localizer) 도입 및 단일 책임 원칙(SRP) 기반 언어/로그 설정 분리 (규칙 1.4.1, 1.5.1, 4.2 준수)**:
  - `Localizer`: 다국어 언어 코드 정규화, 전역 언어 설정 관리 및 범용 다국어 리소스 파일 경로 탐색(`resolve_localized_file`, `resolve_localized_path_from_list`) 전담 모듈 신설.
  - `Localizer`에서 `logging` 설정 딕셔너리, 로깅 환경변수(`AGENT_LOG_LANGUAGE`), 하드코딩된 `logging_messages` 파일명 및 로그 레벨 의존성을 전면 분리 제거.
  - `ConfigLoader`: 로깅 전용 환경변수(`AGENT_LOG_LANGUAGE`, `LOGGING_LANGUAGE`) 및 `logging.language_str` 파싱 전담 메서드(`_resolve_logging_language`) 분리 및 `Localizer` 연계.
  - `ProjectLogger`: `APP_DEFAULT_SCHEMA_DICT`의 기본 로깅 언어를 `KR`로 확정하고, 로그 레벨 탐색, 포매팅 및 에러 설명 정제 전담.
- **국가/언어 코드 표준 규격 통일 (`KR`, `JP`, `EN`, `ZH`)**:
  - 매뉴얼 디렉토리(`manual/kr/`, `manual/jp/`), 파일명(`*_kr.md`, `*_jp.md`), README(`README_KR.md`, `README_JP.md`)와 통일하여 기본 언어 코드를 `KO`에서 `KR`로 변경.
  - `default_agent_common.yml` 및 `config.yml`의 `logging.language_str`을 `KR`로 기본값 지정.
  - `logging_messages_kr.yml`, `logging_messages_zh.yml`, `logging_messages_jp.yml` 추가로 4개 국어(KR, EN, ZH, JP) 표준 로그 메시지 템플릿 완비.
  - `CHANGELOG_KR.md` 생성 및 전체 문서 네비게이션 표준화.
- **배포판 모듈(`load_util.py`, `ig_gcs_bigquery_insert.py`) 언어 설정 `KR` 고정 및 간소화**:
  - 배포판 환경에서 언어 설정을 `KR`로 고정하고 불필요한 다국어 탐색 분기 및 휴리스틱 코드 제거.

### v0.4.91 (2026-10-03)

- **로깅 표준 규격 정비, 래퍼 함수 제거 및 모듈 동기화 (규칙 1.3.1, 1.4.6, 1.5.3, 1.6.1, 4.2 준수)**:
  - `logging.format_str`: 파이썬 표준 `LogRecord` 내장 속격(`%(asctime)s`, `%(levelname)s`, `%(name)s`, `%(filename)s:%(lineno)d`, `%(message)s`)과 유일한 커스텀 주입 속성인 `%(caller_str)s` 체계로 확정.
  - `SingleLineFlattenFormatter`: 불필요하게 파이썬 표준 속성을 중복 복제하던 껍데기 메서드 `formatMessage`를 완전 영구 삭제 (규칙 1.4.6 준수).
  - `logging.log_file_str`: 경로 템플릿 인자를 정규 타입 접미사 `{app_name_str}`, `{log_level_str}`로 확정하고, 불필요한 대소문자/약칭 방어 파라미터(`APP_NAME`, `LOG_LEVEL`, `app_name`, `log_level`) 및 임시 변수 완전 제거.
  - `_safe_log_record_factory` 및 로거 레코드 속성에서 비표준/레거시 별칭(`record.className`, `record.caller`, `fallback_class_name`)을 전면 삭제하고 `record.class_name_str`, `record.caller_str`, `fallback_class_name_str`로 단일화.
  - `ProjectLogger.configure`: 극초기 레거시 서드파티 로거(`metricflow`, `metricflow_semantics`, `urllib3`, `httpx`) 강제 레벨 억제 하드코딩 완전 삭제.
  - `load_util.py` 내의 `SingleLineFlattenFormatter` 및 `ProjectLogger.configure`를 `agent_common/logger.py`와 100% 동일하게 일치시키고 하드코딩된 폴백 코드 상수(Fail-Fast 규칙 1.3.1 위반) 완전 척결.

### v0.4.90 (2026-10-01)

- **`BigQueryClient.get_existing_records_metadata` 메서드 신규 구현 (규칙 1.4, 1.5, 4.2 준수)**:
  - BigQuery 테이블에서 주어진 PK 목록에 해당하는 레코드들의 메타데이터(상태코드 `asstStusCd`, 수정일시 `orignAmndHms` 등)를 고속으로 일괄 조회하여 `{pk_str: {컬럼명: 값}}` 딕셔너리로 반환하는 메서드 신설.
  - BigQuery API 요청 크기 한도(HTTP 413) 방지를 위해 `UNNEST(@pk_list)` 기반 5,000건 청크 분할 쿼리 실행 구조 적용.
  - 사전 정의된 로깅 메시지(`db_existing_records_loaded`, `existing_records_metadata_fetch_failed`)와 100% 일치시켜 조회 성공 및 예외 발생 시 표준 로그 출력 완비.

### v0.4.89 (2026-10-01)

- **설정 로더 및 래퍼 재귀 함수 자원 과다 사용(CWE-674) 방어 조치 (규칙 1.3, 1.4, 4.2 준수)**:
  - Sparrow(스패로우) 정적 분석 도구의 '종료되지 않는 반복문 또는 재귀 함수' 취약점 지적에 대응하여 `ReadOnlyConfig.register_schema`, `ReadOnlyConfig.apply_cli_overrides`에 최대 깊이 제한(`max_depth_int=10`) 및 명시적 기저 조건 탈출 반환문(Early Return) 완비.
  - `ConfigLoader._deep_merge` 및 `ConfigLoader._interpolate_env_vars` 내부 재귀 로직에 최대 탐색 깊이 제한(`max_depth_int=20`) 및 타입 불일치/깊이 초과 시 즉시 탈출하는 가드 절을 적용하여 스택 오버플로우 및 무한 루프 위험 원천 차단.

### v0.4.88 (2026-10-01)

- **`BigQueryClient.convert_to_bigquery_datetime` 메서드 신규 구현 (규칙 1.4, 4.2 준수)**:
  - BigQuery의 `DATETIME` 데이터 타입 적재 규격에 맞추어 다양한 원천 일시 문자열(ISO8601, 공백 구분, 14자리/8자리 숫자 등)을 순수 벽시계 시각(`YYYY-MM-DD HH:MM:SS`)으로 변환하는 메서드 신설.
  - BigQuery `DATETIME`은 타임존 오프셋(`+09:00`, `Z` 등) 포함 시 파싱 오류를 유발하므로 타임존 오프셋을 배제하며, 명시적 타임존 포함 데이터는 한국 시각(KST)으로 정규화 변환 후 반환.

### v0.4.87 (2026-10-01)

- **`_SafeNamespace` 무한 재귀(`RecursionError`) 결함 원천 해소 (규칙 1.3, 1.4, 4.2 준수)**:
  - `_SafeNamespace.__getattr__` 및 내부 매직 메서드에서 `hasattr(self, "_data")` 호출 시, `_data` 속성이 없을 때 `__getattr__`가 재귀적으로 호출되어 발생하던 `RecursionError: maximum recursion depth exceeded` 결함 원천 차단.
  - `self.__dict__.get("_data")` 직접 접근 방식으로 전면 전환하여 매직 메서드 재귀 호출 위험을 0%로 제거하고, 인스턴스 초기화 시 `self._data = None` 기본 속성을 명시적으로 보장.

### v0.4.86 (2026-10-01)

- **`SingleLineFlattenFormatter` 및 로거 계층 단일 책임 원칙(SRP) 구조 분리 (규칙 1.4.1, 4.2 준수)**:
  - `SingleLineFlattenFormatter` 내부에 혼재되어 있던 호출 스택 검사 및 `caller`(`ClassName.funcName()`) / `className` 추출 루틴을 로거 계층(`logging.setLogRecordFactory`, `_safe_log_record_factory`)으로 완전 이관.
  - `LogRecord` 생성 시점에 `caller`와 `className`이 항상 채워지도록 보장하여, 포매터의 종류(기본 `Formatter`, `SingleLineFlattenFormatter` 등)와 무관하게 `%(caller)s` 누락으로 인한 `KeyError` 원천 차단.
  - `SingleLineFlattenFormatter`는 개행 평탄화(`\n` -> 공백) 및 최종 문자열 포맷팅이라는 본연의 책임만 순수하게 전담하도록 구조 최적화.

### v0.4.85 (2026-10-01)

- **`TimeUtils.format_elapsed_time` 소요시간 포맷팅 유틸리티 메서드 신설 (규칙 1.4, 4.2 준수)**:
  - 파이프라인 단계별 및 전체 작업 실행 소요시간(초)을 가독성 높은 시간 문자열(예: `1h 23m 45.67s`, `2m 15.30s`, `4.25s`)로 변환하는 클래스 메서드 추가.

### v0.4.84 (2026-09-30)

- **`_SafeNamespace(dict)` 통합 및 Fail-Fast 실현 (규칙 1.5.3, 1.4.6, 4.2 준수)**:
  - 대소문자 무시(case-insensitive) 탐색 및 빈 문자열(`""`) 침묵 반환 방어 코드를 전면 제거하고, 필드 누락 시 `AttributeError` / `KeyError`를 발생시켜 Fail-Fast 실현.
  - `dict` 상속 매핑 클래스로 구조화하여 `eval()`의 로컬 변수 사전(Locals) 역할과 점(.) 속성 접근을 단일 클래스로 통합 전담.
  - `agent_common` 최상위 패키지(`__init__.py`)에 `_SafeNamespace`를 공식 공개(`__all__`)하여 애플리케이션의 중복 클래스 정의를 원천 제거.

### v0.4.83 (2026-09-29)

- **`utils.py` 순환 참조(Circular Import) 결함 원천 해소 및 단일 책임 원칙(SRP) 기반 모듈 분리 (`time_utils.py`, `progress_tracker.py`, `table_formatter.py`) (규칙 1.4.1, 1.5.3, 4.2 준수)**:
  - `TimeUtils`: 호스트 시스템 로컬 타임존 동적 감지, 세계 표준시 해석 및 일시 파싱 전담 코어 인프라 모듈(`agent_common.time_utils`)로 완전 독립 (설정 로더 의존성 제로화).
  - `ProgressTracker`: 배치 작업 실시간 진행률 추적, 처리 속도 및 남은 시간(ETA) 계산, 마일스톤 경고 로깅 전담 모듈(`agent_common.progress_tracker`)로 분리.
  - `TableFormatter`: 마크다운 및 모노스페이스 콘솔 표 세로줄 정렬 및 전각/반각 표시 폭 계산 전담 모듈(`agent_common.table_formatter`)로 분리.
  - `config_loader.py`: 도메인 도구(`DateTimeUtils`)에 대한 최상단 모듈 레벨 임포트를 제거하고 `ensure_config_file()` 내 지연 로딩(Lazy Import)으로 전환하여 루트 설정 인프라와 상위 도구 계층 간의 의존성 역전 및 순환 참조 원천 차단.
  - **레거시 모듈 임포트 정규화 (규칙 1.5.3 준수)**: 기존 `utils.py`에 대한 하위 호환 포워딩 임포트 생성을 배제하고, `clients.py`, `logger.py`, `date_time_utils.py`, `ecs_to_gcs.py` 및 단위 테스트 모듈들의 임포트 경로를 정규 신규 모듈(`time_utils`, `progress_tracker`, `table_formatter`)로 전수 현행화.

### v0.4.82 (2026-09-28)

- **입력 파라미터 및 일자 유효성 검증 표준 로깅 템플릿 신설 (`validation` 섹션) (규칙 1.1, 1.5.1, 1.6.1 준수)**:
  - `invalid_date_format`: 입력 일자 형식 오류 안내 (`key_str`, `val_str`, `message_str`).
  - `invalid_date_range`: 입력 일자 범위 오류 안내 (`start_date_str`, `end_date_str`, `message_str`).
- **설정 파일 자동 생성/보정 및 BigQuery 테이블 메타데이터 로깅 템플릿 정식 등록**:
  - `config_auto_create_failed`, `config_auto_repair_failed`: 설정 파일 자동 생성/보정 실패 로깅 템플릿 정식 등록 (`file_path_str`, `error_str`).
  - `table_get_failed`, `table_metadata_update_failed`, `table_timestamp_mode_mismatch`: BigQuery 테이블 메타데이터 조회/갱신 및 모드 검증 로깅 템플릿 정식 등록.
  - `storage_clean_failed`: 기존 비표준 특정 벤더명 키(`gcs_clean_failed`)를 `storage_type_str` 기반 범용 키로 일원화.
  - `storage_date_folder_purge_error`: 기존 `storage_date_folder_clean`(INFO) 및 `storage_date_folder_purged`(WARNING)와 쌍을 이루는 날짜 폴더 잔여 정리 실패 에러 템플릿 정식 등록.
- **공통 라이브러리 순수성 강화 및 애플리케이션 특화 로그 분리 (규칙 1.5.1 준수)**:
  - ECS/GCS 파이프라인 종속적(ECS_Key, GCS_Blob)인 `storage_direct_upload_failed`를 `agent_common`에서 제거하고, 개별 애플리케이션 설정(`config/logging_messages.yml`)으로 분리 이관하여 중복 및 도메인 결합(Coupling) 해소.
- **로깅 템플릿 플레이스홀더 및 소스코드 호출부 kwargs 전수 타입 접미사(`_str`, `_int` 등) 표준화 (규칙 1.6.1 준수)**:
  - `clients.py`, `config_loader.py`, `error_handler.py`, `llm.py`, `tool_parser.py` 전수 리팩토링.

### v0.4.81 (2026-09-28)

- **테이블 WRITE_TRUNCATE 카운트다운 및 분할 배치 적재 범용 로깅 템플릿 추가 (`logging_messages_ko.yml`, `logging_messages_en.yml`) (규칙 1.5.1, 4.2 준수)**:
  - `table_truncate_countdown`, `table_truncate_tick`, `table_truncate_countdown_completed`: 대량 데이터 유실 방지를 위한 WRITE_TRUNCATE 적재 카운트다운 타이머 및 완료 안내 템플릿 신설.
  - `db_bulk_load_batch_started`, `db_bulk_load_batch_completed`: 대량 행(Bulk) 분할 배치(청크) 로드 진행 및 완료 안내 템플릿 신설.

### v0.4.80 (2026-09-23)

- **Google Cloud BigQuery WHERE 조건 기반 안전 삭제(DELETE DML) 메서드 추가 (`clients.py` - `BigQueryClient`) (규칙 1.1, 1.3, 1.6.1 준수)**:
  - `delete_rows(where_clause_str, timeout_int=None) -> int`: 지정된 조건식(WHERE 절)에 해당하는 BigQuery 대상 테이블의 행(row)들을 `DELETE FROM ... WHERE ...` DML로 일괄 삭제하고, 실제 삭제된 행 개수(`affected_rows_int`)를 반환하는 메서드 신설.
  - **전체 삭제 방지 조기 실패(Fail-Safe / Fail-Fast)**: `where_clause_str`가 비어있거나 무조건 참(`1=1`, `TRUE`, `''=''` 등)인 위험 조건 유입 시 `ValueError` 즉시 발생 및 실행 차단.
  - `logging_messages_ko.yml` 및 `logging_messages_en.yml`: BigQuery 테이블 데이터 정리 및 삭제 관련 표준 로깅 템플릿(`db_delete_started`, `db_delete_completed`, `db_delete_failed`) 등록.

### v0.4.79 (2026-09-22)

- **Google Cloud Storage (GCS) 일괄/단일 삭제 메서드 추가 (`clients.py` - `GcsClient`)**:
  - `delete_blobs_by_prefix(prefix_str, batch_size_int=1000)`: 지정된 접두사(prefix) 하위의 모든 blob을 GCS Batch API를 통해 고속 일괄 삭제하는 메서드 신설.
  - `delete_blob(destination_blob_name_str)`: 단일 blob 객체 삭제 메서드 신설.
  - `logging_messages_ko.yml`: GCS 데이터 정리 및 삭제 관련 표준 로깅 템플릿(`gcs_clean_started`, `gcs_clean_prefix_completed`, `gcs_clean_completed`, `gcs_clean_failed`) 등록.

### v0.4.78 (2026-09-21)

- **AI 개발 요청 가이드 및 통합 LLM 사용 설명서 추가**:
  - README에 만들려는 기능, PyPI·GitHub 링크, 참고 기능 번호를 전달하는 요청 예시와 최소 기능부터 단계적으로 확장하는 방법을 추가했습니다.
  - `manual/kr/llm/01_unified_llm_client.md`와 영문 매뉴얼을 추가했습니다. 모델 프로필, 외부 API·Fabrix·로컬 GGUF 설정, 환경변수, 반환값·예외 처리 범위를 설명합니다.
  - Antigravity Stop 훅과 Groq 감독관 AI의 `AGENTS.md` 검사 사례, 검사 범위·생략 조건, `LlmClient` 적용 시 차이를 문서화했습니다.
  - README의 7번 항목과 매뉴얼 표에 문서를 연결하고, 개발 중인 6번 에러 핸들러 소개를 제외했습니다.
  - `auto` 모드는 외부 호출이 `None`을 반환할 때만 로컬로 전환한다는 실제 동작에 맞춰 설명을 수정했습니다.
  - 배포 버전 및 README 명령 예시를 `0.4.78`로 갱신했습니다. 런타임 동작 변경은 없습니다.

### v0.4.77 (2026-09-18)
- **동적 도구 로더 및 템플릿 평가기(`tool_parser.py`) & 내장 도구(`tool/date/date_time_utils.py`), 공용 유틸리티(`utils.py`) 상세 기술 매뉴얼(한국어/영어 14종) 신설 및 README.md 전면 갱신 (규칙 2.1, 4.2 준수)**:
  - `manual/kr/tool_parser/` 및 `manual/en/tool_parser/` 신설:
    - `01_dual_tool_hierarchy_discovery.md`: 4.1. 이원화된 Tool 디렉터리 계층 탐색(1순위: 내장 `agent_common/tool/` vs 2순위: 프로젝트 로컬 `config.transfer.tool_dir_str`), 3단계 함수 탐색 알고리즘, `_tool_cache` 인메모리 캐싱, 기동 초기 `scan_rules_for_tool_functions` 사전 Fail-Fast 검증.
    - `02_declarative_template_eval.md`: 4.2. 선언적 템플릿 치환 및 표현식 평가(`ToolParser.eval`), 단일 함수 직통 호출, 점(`.`) 네임스페이스 바인딩, 파이프(`|`) 다중 폴백 우선순위, `inspect.signature` 기반 파라미터 매핑 및 `ctx` 컨텍스트 자동 주입.
    - `03_safe_namespace_navigation.md`: 4.3. 안전한 네임스페이스 탐색(`_SafeNamespace`), 점(`.`) 및 인덱스(`[]`) 접근 통합, 대소문자 무관(Case-insensitive) 탐색, 결측 키에 대한 빈 문자열(`""`) 안전 반환, 중첩 컬렉션 재귀 래핑.
    - `04_builtin_datetime_utils.md`: 4.4. 내장 공통 일시 도구(`DateTimeUtils`), 비즈니스 테이블 룰(`table_rules.yml`) 및 템플릿 치환식 지원, `TimeUtils` 코어 인프라 위임 및 역할 분담, `YYYYMMDD`, ISO 타임스탬프, 압축 일시(`YYYYMMDDHHMMSS`), 표시용 일시 생성.
  - `manual/kr/utils/` 및 `manual/en/utils/` 신설:
    - `01_time_utils_and_timezone_resolution.md`: 5.1. 호스트 시스템 타임존 감지 및 전 세계 표준시 해석(`TimeUtils`), 호스트 OS/컨테이너 타임존 동적 감지(`get_system_timezone`, `get_system_timezone_offset_str`), 30여 개 주요 글로벌 타임존 약어(`WORLD_TIMEZONE_OFFSETS_DICT`) 및 오프셋 해석(`resolve_timezone`), timezone-aware datetime 정규화(`parse_datetime`).
    - `02_progress_tracker_and_milestones.md`: 5.2. 멀티스레드 실시간 진행률 추적 및 마일스톤 경고(`ProgressTracker`), 배치 대용량 파일/데이터 처리 실시간 추적, 처리 속도(건/s, MB/s) 및 남은 시간(ETA) 동적 계산, 일반 진행 `INFO` vs 10% 배수 마일스톤 및 완료 시 `WARNING` 승격 로깅.
    - `03_unicode_table_formatter.md`: 5.3. 유니코드 전각 문자 폭 계산 및 마크다운/콘솔 테이블 칼맞춤 포매터(`TableFormatter`), `unicodedata.east_asian_width` 기반 동아시아 전각(2칸) vs 반각(1칸) 정밀 계산, 마크다운 표 헤더/구분선/데이터 행 세로줄 오차 없는 정렬.
  - `README.md`:
    - 국문/영문 주요 기능 섹션 4번 및 5번에 4.1 ~ 4.4, 5.1 ~ 5.3 매뉴얼 링크 및 세부 기능 상세 설명 추가.
    - 국문/영문 상세 기능 매뉴얼 표(User Manuals Table)에 4.1 ~ 4.4, 5.1 ~ 5.3 행 신규 추가.
    - 패키지 빌드 및 배포 버전 `0.4.77` 최신화.
  - `agent_common/__init__.py` 및 `pyproject.toml` 버전 `0.4.77` 갱신.

### v0.4.76 (2026-09-16)
- **클라우드 스토리지 및 데이터베이스 클라이언트(`clients.py`) 상세 기술 매뉴얼(한국어/영어 10종) 신설 및 README.md 전면 갱신 (규칙 2.1, 4.2 준수)**:
  - `manual/kr/clients/` 및 `manual/en/clients/` 신설:
    - `01_s3_ecs_storage_client.md`: 3.1. AWS S3 및 Dell ECS 오브젝트 스토리지 연동, `head_bucket` Fail-Fast 검증, 대용량 페이징 순회, GCS 실시간 스트리밍 전송 및 동일 크기 파일 스마트 스킵(`transfer_to_gcs`).
    - `02_gcs_cloud_storage_client.md`: 3.2. Google Cloud Storage 스트리밍 업로드 및 4단계 인증 우선순위(`GOOGLE_APPLICATION_CREDENTIALS_JSON` 인메모리 JSON -> `GOOGLE_APPLICATION_CREDENTIALS` 파일 -> `credentials_path_str` -> Google ADC), 메모리 절약형 스트림 업로드(`upload_stream`).
    - `03_bigquery_batch_and_streaming_load.md`: 3.3. Google Cloud BigQuery 배치 적재(`load_table_from_json_data`) vs 실시간 스트리밍 인서트(`insert_rows_json_data`), 중첩 에러(`errors`, `location`, `reason`) 분해 진단, 중복 전송 방지 키 조회(`get_existing_keys`), SQL 쿼리(`query`).
    - `04_bigquery_inline_merge_upsert.md`: 3.4. BigQuery 고성능 인라인 MERGE (Upsert) 엔진, 스테이징 테이블 없는 `UNNEST(JSON_QUERY_ARRAY(@json_payload))` 파라미터 바인딩, 자동 타입 추론 및 캐스팅(`column_types_dict`), 최초값 보존(`preserve_columns_list`), 백틱(`` ` ``) 컬럼명 보호, 100건 청크 분할.
    - `05_bigquery_timestamp_and_tz_sync.md`: 3.5. BigQuery 타임스탬프 변환 및 테이블 타임존 모드 정합성 검증·동기화 (`convert_to_bigquery_timestamp`, `validate_and_sync_table_timestamp_mode`), Standard-UTC vs KST-as-UTC 모드.
  - `README.md`:
    - 국문/영문 주요 기능 섹션 3번에 3.1 ~ 3.5 매뉴얼 링크 및 세부 기능 상세 설명 추가.
    - 국문/영문 실전 사용 예시 섹션에 스토리지 및 BigQuery 클라이언트 코드 블록 추가.
    - 국문/영문 상세 기능 매뉴얼 표(Table)에 3.1 ~ 3.5 행 추가.
    - 패키지 빌드 및 배포 버전 `0.4.76` 최신화.

### v0.4.75 (2026-09-16)
- **BigQueryClient KST 표시용 타임스탬프(KST-as-UTC) 모드 및 테이블 타임존 정합성 검증(Fail-Fast) 신설 (규칙 1.1, 1.3, 1.6.1 준수)**:
  - `agent_common/clients.py` (`BigQueryClient`):
    - `kst_as_utc_timestamp_bool` 설정 옵션 연동: 고객사 화면 표시 요구에 따라 KST 시각 숫자를 그대로 유지하며 `+00:00`(UTC)으로 적재하여 BigQuery 콘솔에서 한국 시각 수치(`... UTC`)로 표시되도록 지원.
    - `convert_to_bigquery_timestamp`: KST-as-UTC 모드 활성화 시 명시적 타임존 및 naive 일시를 KST 기준으로 정규화한 뒤 `+00:00` 오프셋 부여.
    - `validate_and_sync_table_timestamp_mode(write_disposition_str)`:
      - 테이블이 비어있거나(`num_rows == 0`) `WRITE_TRUNCATE` 실행 시: 테이블 라벨(`timestamp_mode: "kst_as_utc"` 또는 `"standard_utc"`), 테이블 설명 및 TIMESTAMP 타입 컬럼 설명을 신규 모드에 맞추어 자동 갱신.
      - 기존 데이터가 존재하는 테이블의 경우: 기등록된 `timestamp_mode` 라벨과 현재 설정 불일치 시 즉시 **Fail-Fast**(`ValueError`)를 발생시켜 9시간 시차 혼재에 의한 데이터 오염 원천 차단.

### v0.4.74 (2026-09-15)
- **`TimeUtils.parse_datetime` 및 `DateTimeUtils.parse_datetime` 공용 일시 정규화 유틸리티 추가 (규칙 1.5.1, 1.4.6 준수)**:
  - `agent_common/utils.py` (`TimeUtils`):
    - `parse_datetime(dt_input_any: Any, default_tz_obj: Optional[timezone] = None) -> Optional[datetime]` 클래스 메서드 신설.
    - 다양한 형태(datetime 객체, ISO 8601 일시 문자열, naive/aware 등)의 일시 값을 표준 비교 및 연산이 가능한 `timezone-aware datetime` 객체로 정규화 변환.
    - 문자열 'Z'의 '+00:00'(UTC) 안전 변환 및 naive datetime 대상 시스템 기본 타임존 자동 보정 지원.
  - `agent_common/tool/date/date_time_utils.py` (`DateTimeUtils`):
    - 룰 파서 및 외부 공용 편의성을 위해 `parse_datetime` 인터페이스 노출 및 `TimeUtils.parse_datetime` 위임 연결.
  - `app/ecs_to_gcsbigquery_merge.py`:
    - 개별 애플리케이션 내부에 중복 정의되어 있던 `_parse_timestamp_to_datetime` 메서드를 전면 제거하고 `TimeUtils.parse_datetime` 공용 유틸리티 직접 호출로 통합.

### v0.4.73 (2026-09-15)
- **`ProjectLogger` 로깅 메서드 `default_str` 표준 타입 접미사 파라미터화 및 전달 정합성 확립 (규칙 1.5.3, 1.6.1 준수)**:
  - `agent_common/logger.py`:
    - `info`, `warning`, `error`, `critical`, `debug`, `exception`의 기본 템플릿 매개변수 명칭을 `default: str`에서 `default_str: str = ""`로 표준화.
    - 내부 `get_log_msg()` 호출 시 `default_str=default_str`로 정확히 바인딩하여, YAML 템플릿 미등록 시 지정된 기본 템플릿(예: `default_str="{summary}"`)이 유실되고 메시지 코드 식별자만 출력되던 결함 원천 해결.
    - 방어 코드(`kwargs.pop("default")` 등)를 일체 배제하고 명시적인 `default_str` 단일 표준으로 정합성 확립.

### v0.4.72 (2026-09-15)
- **`S3Client.transfer_to_gcs` 반환값 타입 확장 및 GCS 기존재 스킵 상태(`SKIPPED`) 명확화 (규칙 1.5.3, 1.6.1 준수)**:
  - `agent_common/clients.py`:
    - `S3Client.transfer_to_gcs()`의 반환값 타입을 `bool`에서 `str`(`"UPLOADED"`, `"SKIPPED"`, `"FAILED"`)로 확장.
    - 기존 GCS 버킷에 동일 파일(크기 일치) 존재 시 단순 성공(`True`) 대신 `"SKIPPED"`를 명시 반환하여, 호출자(파이프라인 매니저 및 요약 리포터)에서 신규 전송 건과 기전송 제외(스킵) 건을 명확히 구분 집계할 수 있도록 개선.
    - 신규 스트리밍 전송 성공 시 `"UPLOADED"`, 예외 발생 시 `"FAILED"` 반환.

### v0.4.71 (2026-09-15)
- **`BigQueryClient` 타임존 오프셋 우선순위 정상화 및 기본값 `+09:00` 설정 (규칙 1.1.1, 1.3, 1.4.2 준수)**:
  - `agent_common/clients.py`:
    - `BigQueryClient.__init__`: 호스트 시스템이 UTC(`+00:00`) 환경이더라도 `config.bigquery.timezone_offset_str`에 명시적인 타임존 오프셋(`+09:00` 등)이 지정되어 있으면 이를 최우선 적용하도록 분기 로직 정상화.
    - `APP_DEFAULT_SCHEMA_DICT`: `bigquery.timezone_offset_str` 기본값을 국내 업무 원천 데이터 표준에 맞추어 `+09:00`으로 명시.
    - Airflow 파드(UTC) 환경에서 한국 시간(KST) 원천 데이터 적재 시 9시간 시차 왜곡이 발생하던 현상을 원천 차단.

### v0.4.70 (2026-09-15)
- **`utils.py` 내 `DateTimeUtils` 하위 호환성 재노출(Re-export) 전면 제거 및 순환 참조(Circular Import) 원천 소멸 (규칙 1.4.6, 1.5.3 준수)**:
  - `agent_common/utils.py`:
    - 모듈 하단에 존재하던 `from agent_common.tool.date.date_time_utils import DateTimeUtils` 지연 임포트 및 `__all__` 내 `"DateTimeUtils"` 노출을 완전히 제거.
    - `agent_common/__init__.py` -> `date_time_utils.py` -> `utils.py` -> `date_time_utils.py`로 이어지던 부분 초기화 순환 참조(Circular Dependency)를 원천 차단하고 `date_time_utils` -> `utils` 단방향 DAG 구조 확립.
    - 하위 호환성 껍데기 코드를 전면 배제하고, `DateTimeUtils` 사용처는 최상위 `agent_common` 단일 표준 진입점으로 일원화.

### v0.4.69 (2026-09-14)
- **`TimeUtils` 코어 인프라 분리, `DateTimeUtils` 실체화 및 껍데기 함수(Pass-through Wrapper) 전면 제거 (규칙 1.1.1, 1.2.1, 1.4.1, 1.4.6 준수)**:
  - `TimeUtils` (`agent_common/utils.py`):
    - 호스트 시스템(OS/컨테이너) 로컬 타임존 동적 감지(`get_system_timezone`), ISO 8601 오프셋 변환(`get_system_timezone_offset_str`, `format_timezone_offset`), 전 세계 표준시 사전(`WORLD_TIMEZONE_OFFSETS_DICT`), 유연한 타임존 해석기(`resolve_timezone`)를 전담하는 코어 시간 인프라 클래스 신설.
    - 단순 1줄 위임 호출을 수행하던 껍데기 함수(`resolve_default_timezone`)를 완전히 제거하고 `resolve_timezone()`이 기본 인자(`None`)를 직접 해석하도록 일원화(규칙 1.4.6 준수).
  - `DateTimeUtils` (`agent_common/tool/date/date_time_utils.py`):
    - 룰(`table_rules.yml`), `ToolParser`, 데이터 파이프라인에서 실제 호출되는 필수 메서드만 남기고 코드 경량화(276줄 -> 85줄).
    - 실제 사용 메서드: `get_now_datetime(tz_obj)`, `get_today_yyyymmdd(tz_obj)`, `get_now_timestamp(tz_obj)`, `get_now_no_tz(tz_obj)`, `get_now_compact(tz_obj)`.
    - 실제 프로젝트 어디에서도 사용되지 않던 미사용·추측성 메서드(`get_yesterday_yyyymmdd`, `get_now_formatted`, `parse_date_to_yyyymmdd`, `format_timestamp`, `add_days`, `date_diff_days`, `is_expired`, `format_timezone_offset`) 및 미참조 포맷 상수(`FORMAT_DATETIME_STD_STR`, `FORMAT_DATETIME_ISO_STR`) 전면 제거 (규칙 1.4.5, 1.5.2 추측성 코딩 금지 및 KISS/YAGNI 준수).
    - 모듈 하단에 존재하던 단순 포워딩 편의 함수 7개(`get_today()`, `get_now_compact()` 등)를 전면 제거하고 `ToolParser`의 클래스 메서드 자동 탐색 엔진을 활용하도록 단순화(규칙 1.4.6 준수).
  - `ToolParser` (`agent_common/tool_parser.py`):
    - KISS 및 YAGNI 원칙에 따라 중복되고 불필요한 시스템 컨텍스트 조립 메서드 `build_sys_context()` 및 `schemas/sys.json`을 완전히 제거.
    - `eval()` 내 매번 발생하던 불필요한 기본 컨텍스트 병합 오버헤드를 제거하여 템플릿 평가 성능 최적화.
    - 날짜/시간 도구는 `{DateTimeUtils.get_now_timestamp()}`, `{DateTimeUtils.get_today_yyyymmdd()}`로 직통 호출하도록 일원화.
  - `ProgressTracker` (`agent_common/utils.py`):
    - 호출부가 전무하고 `ProjectLogger.log_summary()` 및 도메인 전용 리포터와 역할이 중복되던 미사용 레거시 메서드 `summary()`를 완전히 제거 (KISS, YAGNI, 규칙 1.4.5 준수).
    - `__init__` 내 불필요한 별칭 인스턴스 변수(`self.logger`)를 제거하고 `self.logger_obj`로 단일화 (규칙 1.5.3 준수).
  - `TableFormatter` (`agent_common/utils.py`):
    - `format_markdown_table` 메서드를 복원 및 `format_row`, `format_separator`와 연동하여 마크다운 테이블 자동 맞춤 서식화 보장.
  - `BigQueryClient` (`agent_common/clients.py`):
    - 호스트 시스템 시간이 UTC인 환경(Airflow 파드)에서는 타임존 왜곡 방지를 위해 `timezone_offset_str` 기본값을 `+00:00`으로 자동 적용하고, `config.yml`의 `timezone_offset_str`가 "AUTO" 또는 비어있을 때 시스템 로컬 타임존 오프셋을 동적으로 반영하도록 개선.

### v0.4.68 (2026-09-14)
- **`DateTimeUtils` 타임존 오프셋 하드코딩 전면 제거, 동적 포매터 `format_timezone_offset` 신설 및 `sys.now` 타임존 표준화 (규칙 1.1.1, 1.4.1 준수)**:
  - `DateTimeUtils` (`agent_common/tool/date/date_time_utils.py`):
    - `FORMAT_DATETIME_STD_STR` 상수 내 `+09:00` 하드코딩을 제거하고 `%Y-%m-%d %H:%M:%S%z`로 전환하여 규칙 1.1.1(하드코딩 금지) 엄격 준수.
    - `format_timezone_offset(dt_obj)` 클래스 메서드를 신설하여 `datetime` 객체로부터 실제 적용된 타임존 오프셋(`+09:00`, `+00:00`, `-05:00` 등)을 ISO 8601 콜론 규격으로 동적 추출 및 결합.
    - `resolve_default_timezone()` 클래스 메서드를 신설하여 환경변수(`TIMEZONE_OFFSET`, `TZ_OFFSET`) 기반의 동적 타임존 해석 지원.
  - `ToolParser` (`agent_common/tool_parser.py`):
    - `build_sys_context()`의 `sys.now`를 `FORMAT_DATETIME_NO_TZ_STR` 호출에서 `get_now_formatted()` 호출로 일원화하여, `schemas/sys.json` 명세와 동일하게 타임존 오프셋이 포함된 완전한 ISO 8601 일시(`YYYY-MM-DD HH:MM:SS+09:00`)를 기본 제공하도록 개선.
    - 타임존 없는 표시용 보조 변수로 `sys.now_no_tz`를 추가 제공.

### v0.4.67 (2026-09-14)
- **`DateTimeUtils` 타임존(Timezone-Aware) 인식 및 기본 한국 표준시(KST, UTC+9) 자동 변환 도입 (규칙 1.2.1, 1.4.1 준수)**:
  - `DateTimeUtils` (`agent_common/tool/date/date_time_utils.py`):
    - 파이썬 표준 라이브러리 `datetime.timezone`, `datetime.timedelta` 기반 `DEFAULT_TIMEZONE_OBJ` (KST, UTC+9)를 선언하고, `time.strftime` 기반 OS 시스템 로컬 시간 의존성을 전면 탈피.
    - `get_now_datetime(tz_obj)` 메서드를 신설하여 timezone-aware `datetime` 객체를 반환하도록 지원.
    - `get_today_yyyymmdd(tz_obj)`, `get_now_formatted(fmt_str, tz_obj)`, `get_now_compact(tz_obj)` 메서드에 타임존 변환을 적용하여, Airflow 파드 등 UTC(+00:00) 환경에서 실행되더라도 항상 정확한 한국 시각 및 한국 기준 일자(새벽 배치 날짜 역전 방지)를 산출하도록 보장.
    - `get_now_formatted()`에서 `%z` 기반의 표준 ISO 8601 타임존 오프셋(`+09:00`)을 동적으로 결합하여 반환하도록 개선.

### v0.4.66 (2026-09-14)
- **`__init__.py` 내 `DateTimeUtils` 원본 모듈 직접 임포트 경로 명확화 (규칙 1.4.6 준수)**:
  - `agent_common/__init__.py`:
    - 기존에 `utils.py`를 거쳐 2단계로 간접 참조하던 `DateTimeUtils` 임포트를 본래 정의 위치인 `agent_common.tool.date.date_time_utils`에서 직접 임포트하여 re-export하도록 구조 단순화.
    - IDE의 심볼 자동완성, 정의로 이동(Go to Definition) 및 정적 분석기에서의 심볼 인식 투명성 강화.
    - `utils.py`의 `from agent_common.tool.date.date_time_utils import DateTimeUtils` 하위 호환성 임포트는 그대로 유지하여 기존 코드 호환성 100% 보장.

### v0.4.65 (2026-09-13)
- **`ProgressTracker` 및 `TableFormatter` 설정값 직참조(Direct Immutable Config Access) 구조 개선 및 불필요 인자/정적 바인딩 제거 (규칙 1.4.2, 1.4.6 준수)**:
  - `ProgressTracker` (`utils.py`):
    - `__init__`에서 `interval_percent_int` 인자 및 인스턴스 복제 상태를 제거하고, 불필요한 `getattr`/`APP_DEFAULT_CONFIG_OBJ` 방어적 fallback 체인을 완전히 배제한 뒤 `update()` 메서드에서 `config.progress_tracker.interval_percent_int`를 전역 직접 참조하도록 일원화.
    - 불필요한 단순 전달 껍데기 프로퍼티(`interval_percent_int`)를 전면 제거하여 규칙 1.4.6 준수.
    - `task_name_str` 기본값의 `"작업"` 하드코딩 리터럴을 제거하고 `config.progress_tracker.default_task_name_str` 및 `APP_DEFAULT_SCHEMA_DICT`를 통한 선언적 스키마 기본값 바인딩으로 전환.
    - 미사용 정적 설정 객체(`APP_DEFAULT_CONFIG_OBJ`)를 제거하고 모듈 설정 스키마 정의(`APP_DEFAULT_SCHEMA_DICT`)로 정돈.
  - `TableFormatter` (`utils.py`):
    - 클래스 본문의 불필요한 정적 바인딩 변수(`MIN_CENTER_WIDTH_INT` 등 4개)를 제거하고 `format_markdown_table` 메서드 내부에서 `config.table_formatter.*`를 직접 참조하도록 리팩터링.
  - `default_agent_common.yml`:
    - `transfer` 섹션에 `newfile_archive_extensions_list` 기본값(`egg`, `zip`)을 명시하여 패키지 스키마 일원화.
    - `progress_tracker` 섹션에 `default_task_name_str: "작업"` 기본 스키마 추가.

### v0.4.64 (2026-09-13)
- **`utils.py` 모듈 기본 설정 스키마(`APP_DEFAULT_SCHEMA_DICT`) 신설 및 `TableFormatter`/`ProgressTracker` 매직 넘버 상수화 (규칙 1.1.1, 1.7.5 준수)**:
  - `utils.py`:
    - 파일 최상단에 `APP_DEFAULT_SCHEMA_DICT`를 선언하여 `TableFormatter` 및 `ProgressTracker`의 모든 하드코딩 설정(마크다운 구분선 최소 너비 5/4, 양쪽 콜론 패딩 2/1, 진행률 마일스톤 간격 10%)을 스키마화.
    - `TableFormatter` 클래스 상단에 `MIN_CENTER_WIDTH_INT`, `MIN_DEFAULT_WIDTH_INT`, `CENTER_COLON_PADDING_INT`, `DEFAULT_COLON_PADDING_INT`를 바인딩하여 함수 내부 인라인 매직 넘버(5, 4, 2, 1)를 전면 제거.
    - `ProgressTracker.__init__`의 기본 파라미터 `interval_percent_int`를 스키마 기본값으로 연결.
  - `default_agent_common.yml`:
    - 패키지 기본 YAML 설정 파일에 `table_formatter` 및 `progress_tracker` 섹션 기본값 추가.

### v0.4.63 (2026-09-11)
- **모노스페이스 콘솔 및 마크다운 표 세로줄(|) 자동 맞춤 포매터 `TableFormatter` 신설 및 `log_summary` 연동 (규칙 1.2.1, 1.4.1, 1.4.4 준수)**:
  - `TableFormatter` (`utils.py`):
    - 표준 라이브러리 `unicodedata.east_asian_width`를 활용하여 한글(전각) 2칸, 영문/숫자/반각/트리기호(`├`, `─`, `│`, `└`) 1칸의 실제 표시 너비(Display Width)를 정밀 계산.
    - 각 열의 최대 너비 자동 측정 및 정렬 방향(`:---`, `:---:`, `---:`)에 따른 동적 공백 패딩을 수행하여 Airflow 웹 로그 뷰어 및 콘솔 터미널에서 표 세로줄(`|`)이 일직선으로 완벽 정렬되도록 보장.
  - `ProjectLogger.log_summary` (`logger.py`):
    - 기존 수동 문자열 결합 방식에서 `TableFormatter.format_markdown_table()` 호출 방식으로 전환하여 요약 결과 표의 세로줄 어긋남 현상 원천 해결.

### v0.4.62 (2026-09-11)
- **GCP 인증 및 프로젝트 ID 환경변수를 Google Cloud 표준 규격 및 명확한 목적별 네이밍(`GOOGLE_APPLICATION_CREDENTIALS_JSON`, `GOOGLE_APPLICATION_CREDENTIALS`, `GOOGLE_CLOUD_PROJECT`)으로 전면 표준화 (규칙 1.1.3, 1.4.1, 1.5.1, 1.5.3 준수)**:
  - `_resolve_gcp_credentials`:
    - 비표준 사설 변수명(`GCP_KEYFILE_JSON`)을 전면 폐기.
    - 인메모리 JSON 문자열 주입 시: **`GOOGLE_APPLICATION_CREDENTIALS_JSON`** (1순위, `from_service_account_info`) 지원.
    - 로컬 키 파일 경로 지정 시: Google 공식 표준인 **`GOOGLE_APPLICATION_CREDENTIALS`** (2순위, `from_service_account_file`) 지원.
  - `BigQueryClient._connect`:
    - 비표준 사설 변수명(`GCP_PROJECT_ID`)을 전면 폐기하고, Google 공식 표준 환경변수인 **`GOOGLE_CLOUD_PROJECT`**로 단일화.

### v0.4.61 (2026-09-11)
- **파일 확장자별 2단계 매트릭스 요약 리포트 로그 ID(`extension_matrix_summary_report`) 등록 (규칙 1.1.1, 3.1 준수)**:
  - `logging_messages_ko.yml` & `logging_messages_en.yml`:
    - `WARNING.lifecycle` 섹션에 `extension_matrix_summary_report: "{summary}"` 템플릿 추가.
    - 확장자별 2단계 통계 매트릭스 표 출력 시 로그 ID 누락으로 인해 메시지가 치환되지 않고 로그 ID 문자열만 단독 출력되던 현상 원천 해결.

### v0.4.60 (2026-09-10)
- **`log_summary` 요약 표 하단에 에러/제외 상세 내역(원인 코드 및 설명) 목록 보존 복원 (규칙 1.4.1, 3.1 준수)**:
  - `logger.py`:
    - 표 내부에는 긴 설명문 목록을 우겨넣지 않고 깔끔하게 유지하되, 실패(`failure_count_int > 0`) 또는 제외(`excluded_count_int > 0`) 건수가 발생한 경우에 한하여 **표 하단(표 밖)**에 원인 분석용 세부 내역 목록(`* 코드 (설명): N건`)을 덧붙여 출력하도록 보완.
    - 미사용 상태로 남겨질 뻔했던 `error_counts_dict`, `excluded_counts_dict` 파라미터 및 `get_log_id_description()` 기능의 완벽한 활용성 복원.

### v0.4.59 (2026-09-10)
- **`ProjectLogger` 내 성공/실패/제외 카운트 상태를 `self` 인스턴스 변수로 단일화 (규칙 1.4.1, 1.4.2, 1.4.5 준수)**:
  - `logger.py`:
    - 클래스 레벨 전역 변수(`_success_count_int`, `_failure_count_int`, `_excluded_count_int`)를 전면 삭제.
    - 인스턴스 변수(`self.success_count_int`, `self.failure_count_int`, `self.excluded_count_int`)로 단일화하여 객체지향 책임(SRP) 및 상태 캡슐화 완성.
    - `log_summary()`에서 불필요한 `get_result_counts()` 딕셔너리 우회 조회를 제거하고 `self` 변수를 직접 참조하도록 간소화.
    - `update()`, `reset_result_counts()`, `get_result_counts()`에서 클래스 전역 변수 동기화 및 복잡한 조건 분기 제거.

### v0.4.58 (2026-09-10)
- **`ProjectLogger.log_summary` 마크다운 표(Table) 포맷 개편 및 '전체 = 성공 + 실패 + 제외' 정합성 보장 (규칙 1.4.1, 1.4.5, 3.1 준수)**:
  - `logger.py`:
    - 최종 작업 요약 리포트(`log_summary`)를 기존 텍스트 목록 방식에서 시인성 높은 **마크다운 표(Markdown Table)** 포맷으로 개편.
    - `전체 대상 건수 (Total) = 처리 성공 + 처리 실패 + 처리 제외(Skip)` 공식이 항상 100% 일치하도록 합산 및 비율(%) 자동 산출.
    - 가독성을 저해하던 긴 예외/오류 상세 목록 및 처리 제외 사유 나열을 표 내부에서 배제하고 수치 및 성능 지표 위주로 압축.
    - `extra_lines_list`로 전달된 커스텀 상세 정보(`키 : 값`)를 표의 상세 정보 행으로 자동 매핑 지원.

### v0.4.57 (2026-09-10)
- **`clients.py` 내 레거시 클래스 별칭 `EcsClient = S3Client` 삭제 및 클라이언트 명칭 일원화 (규칙 1.4.5, 1.4.6, 1.6.3 준수)**:
  - `clients.py`:
    - 범용 `S3Client` 전환 완료 후 잔존하던 하위 호환 별칭 `EcsClient = S3Client`를 완전히 삭제하여 불필요한 별칭 레이어를 제거하고 클라이언트 명칭을 `S3Client`로 일원화.
  - `__init__.py`:
    - 최상위 패키지 임포트 및 `__all__` 노출 목록에서 `EcsClient` 제거.
  - `README.md`:
    - `S3Client` 소개 설명에서 `EcsClient` 별칭 하위 호환 관련 안내 문구 정리.

### v0.4.56 (2026-09-10)
- **`GcsClient` 및 `BigQueryClient`에 인메모리 JSON 키(`GCP_KEYFILE_JSON`) 지원 및 파일 경로 100% 호환 인증 확장 (규칙 1.1.1, 1.4.1, 1.5.1 준수)**:
  - `clients.py`:
    - 공통 인증 해석 함수 `_resolve_gcp_credentials`를 신설하여 3단계 우선순위(1순위: `GCP_KEYFILE_JSON` / `GOOGLE_KEYFILE_JSON` 인메모리 JSON ➔ 2순위: `credentials_path_str` 파일 경로 ➔ 3순위: Google ADC) 자동 해결 지원.
    - Airflow K8s Secret 및 Connection(`google_cloud_default`)의 `keyfile_dict`를 인메모리로 안전하게 전달받아 파일 생성 없이 `Credentials.from_service_account_info`로 즉시 인증 가능.
    - 로컬 개발 환경의 파일 기반 인증(`Credentials.from_service_account_file`)과의 100% 하위 호환성 보장.
    - `BigQueryClient` 연결 시 환경변수 `GCP_PROJECT_ID` 또는 `GOOGLE_CLOUD_PROJECT`가 주입되면 프로젝트 ID 최우선 자동 반영.

### v0.4.55 (2026-09-10)
- **`ConfigLoader`에 범용 환경변수 템플릿 치환(`${VAR:-default}`) 기능 추가 (규칙 1.1.1, 1.4.1, 1.5.1 준수)**:
  - `config_loader.py`:
    - `_ENV_VAR_PATTERN` 정규식 및 `_replace_env_match` 헬퍼 함수를 추가하여 YAML 파일 및 설정 딕셔너리 내 모든 문자열의 `${VAR_NAME}` 및 `${VAR_NAME:-default}` 구문을 OS 환경변수로 재귀 자동 치환하는 `_interpolate_env_vars` 기능 구현.
    - 도메인/프로젝트 종속적인 하드코딩 없이 모든 에이전트 및 데이터 파이프라인에서 민감한 인증 정보(Access Key, Secret Key, API URL 등)를 외부 환경변수(Airflow, Kubernetes, Docker 등)로부터 선언적으로 안전하게 주입받을 수 있도록 범용성 보장.

### v0.4.54 (2026-09-10)
- **`ConfigLoader` 및 `ReadOnlyConfig`에서 프로젝트 특정 도메인 결합 제거 및 순수 범용 오버라이드 인터페이스로 정제 (규칙 1.1.1, 1.4.1, 1.5.1 준수)**:
  - `config_loader.py`:
    - `apply_cli_args` 메서드 내에 하드코딩되어 있던 특정 프로젝트(`bucket_test`) 전용 섹션(`transfer`, `bigquery`) 및 도메인 필드(`lodin_dstlc_cd_str`, `write_disposition_str` 등) 매핑 로직을 전면 제거.
    - 도메인 무관 순수 계층 딕셔너리를 설정 트리에 최우선 오버라이드 반영하는 범용 인터페이스인 `apply_cli_overrides(overrides_dict)`를 중심으로 설정 갱신 책임 단일화.
    - 공통 라이브러리인 `agent_common`의 범용성(Agnosticism) 및 SRP(단일 책임 원칙) 완벽 회복.

### v0.4.53 (2026-09-10)
- **`ConfigLoader` 및 `ReadOnlyConfig`에 CLI 인자 통합 취합(`apply_cli_args`, `apply_cli_overrides`) 기능 추가 (규칙 1.4.2, 1.4.4, 1.5.1 준수)**:
  - `config_loader.py`:
    - `ConfigLoader`와 `ReadOnlyConfig`에 `apply_cli_args(args)` 및 `apply_cli_overrides(overrides_dict)` 메서드 추가.
    - 프로그램 진입점(`main`)에서 파싱된 CLI `args`(Namespace 또는 dict)를 전달받아 `limit_int`, `target_type_str`, `target_folder_str`, `lodin_dstlc_cd_str`, `start_date_str`, `end_date_str`, `file_logging_bool`, `save_error_json_bool`, `write_disposition_str` 등의 항목을 전역 `config`에 최우선순위로 일괄 반영.
    - `_cached_settings` 자동 무효화를 통해 애플리케이션 어디서든 `config.*` 점 표기법으로 취합된 최종 유효값을 조회할 수 있도록 단일화하고, 각 프로그램 `main()`의 수동 3항 연산자 폴백 및 매개변수 패스스루 체인을 제거.

### v0.4.52 (2026-09-09)
- **`BigQueryClient.merge_table_from_json_data`에 `matched_condition_str` 조건절 주입 지원 추가 (규칙 1.5.1, 1.6.1 준수)**:
  - `clients.py`:
    - `BigQueryClient.merge_table_from_json_data` 메서드 시그니처에 `matched_condition_str: str | None = None` 파라미터 추가.
    - BigQuery MERGE SQL 템플릿의 `WHEN MATCHED` 절을 `WHEN MATCHED {matched_condition_str} THEN` 형태로 동적 조립하도록 지원하여, 호출자가 원천문서수정시간 비교 등의 도메인 조건을 유연하게 주입할 수 있도록 범용 기능 확장.

### v0.4.51 (2026-09-09)
- **`LlmClient` 내 불필요한 껍데기(Pass-through) 게터 프로퍼티 19종 전면 삭제 및 간결화 (규칙 1.4.5, 1.4.6 준수)**:
  - `llm.py`:
    - `LlmClient` 클래스에서 `model_config` 속성을 단순 위임/전달하던 19개의 미사용 `@property` 게터(`provider_str`, `enabled_bool`, `api_key_env_str`, `base_url_str`, `chat_completions_path_str`, `api_format_str`, `model_str`, `llm_id_int`, `client_env_str`, `user_env_str`, `timeout_seconds_int`, `max_tokens_int`, `temperature_float`, `model_path_str`, `n_ctx_int`, `n_threads_int`, `n_batch_int`, `n_gpu_layers_int`, `verbose_bool`)를 전면 삭제.
    - 불필요한 껍데기 래퍼 계층 약 95라인을 제거하고 모델 설정 접근 경로를 불변 설정 객체인 `self.model_config`로 완전히 단일화하여 아키텍처 간결성 및 YAGNI 원칙 달성.

### v0.4.50 (2026-09-09)
- **`ProjectLogger.configure` 내 방어적 퍼지 탐색 및 레거시 키 폴백 전면 삭제 (규칙 1.5.3 준수)**:
  - `logger.py`:
    - `ProjectLogger.configure`에서 `logging.level_dict` / `logging.level_str` / `logging.level` 3중 체인 및 프로그램명 대소문자/하이픈 퍼지 검색 루프를 전면 제거.
    - `level_dict` 직접 매핑 및 `logging.level_str`로 정규화.
    - 미사용 레거시 키 폴백(`logging.format`, `logging.datefmt`, `logging.file_logging`, `logging.log_file`) 및 `str(...)`, `bool(...)` 방어적 형변환을 완전 삭제하고 정규 타입 접미사 설정 키로 일원화.

### v0.4.49 (2026-09-09)
- **`ReadOnlyConfig` 내 퍼지 접미사 탐색 방어 코드 전면 삭제 및 Fail-Fast 실현 (규칙 1.5.3 준수)**:
  - `config_loader.py`:
    - `ReadOnlyConfig.__getattr__` 및 `__contains__`에서 설정 키의 타입 접미사 자동 탈부착 및 퍼지 탐색 루프(`for suffix_str in ("_str", "_int", ...): ...`)를 전면 삭제.
    - 정규 키(`key_str`)로 직접 딕셔너리를 조회(`data[key_str]`)하여, 미정의 키나 접미사 불일치 유입 시 즉시 `AttributeError`가 발생하도록(Fail-Fast) 조치.
    - `effective_key_str` 등의 중간 불필요 임시 변수를 제거하고 `coerce_type_by_key_suffix(key_str, val_any)`로 단순/명료화.

### v0.4.48 (2026-09-09)
- **클라이언트(`clients.py`) 및 LLM(`llm.py`) 모듈 내 방어적 `**kwargs: Any` 및 `kwargs.get(...)` 전면 삭제 (규칙 1.3.1, 1.5.2, 1.6.1 준수)**:
  - `clients.py`:
    - `S3Client.__init__`, `list_objects`, `get_object_stream`, `get_object_size`, `transfer_to_gcs`: `**kwargs: Any` 및 레거시 인자 호환성 명목의 방어적 폴백 로직(`kwargs.get("prefix")`, `kwargs.get("endpoint_url")` 등)을 전면 제거하고 명시적 타입 접미사 인자(`endpoint_url_str`, `prefix_str` 등)로 완전 고정.
    - `GcsClient.__init__`, `get_blob_size`, `upload_stream`: `**kwargs: Any` 제거 및 명시적 파라미터(`bucket_name_str`, `blob_name_str` 등)로 일원화.
    - `BigQueryClient.__init__`, `load_table_from_json_data`, `insert_rows_json_data`, `query`, `get_existing_keys`: `**kwargs: Any` 및 `write_disp` 등의 방어적 인자 폴백 코드 완전 삭제.
  - `llm.py`:
    - `LlmClient.__init__`, `generate`: `**kwargs: Any` 및 `kwargs.get("prompt")` 등 방어적 래퍼 전면 제거. `prompt_str`, `system_prompt_str` 등 정규 시그니처만 허용하여 잘못된 인자 전달 시 즉시 에러가 발생하도록(Fail-Fast) 조치.

### v0.4.47 (2026-09-09)
- **`LlmClient` 불변 설정 직접 접근 전환, `self` 정적 설정 복제 변수 및 방어적 형변환 전면 제거 (규칙 1.4.2, 1.4.5, 1.6.1 준수)**:
  - `llm.py`:
    - `LlmClient.__init__`에서 19개 정적 설정을 `self` 인스턴스 변수로 중복 복제하던 로직(`self.provider_str = str(...)`, `self.max_tokens_int = int(...)` 등)을 전면 제거하고 `self.model_config`(ReadOnlyConfig) 또는 `config.llm_pool[self.model_name_str]`로 직접 조회하도록 단일화.
    - `int(os.getenv(..., str(self.max_tokens_int)))` 식의 불필요한 우향 방어적 형변환 래퍼를 전면 배제하여 타입 이상 시 조기 감지(Fail-Fast)되도록 정비.
    - `APP_DEFAULT_SCHEMA_DICT["llm"]`에서 인위적 폴백 키(`default_provider_str` 등 19종)를 전면 삭제하여 스키마를 경량화.
    - `LlmClient` 외부 호출 호환성을 위해 `model_config` 기반 프로퍼티 게터(Getter) 제공.
  - `llmpool.yml`:
    - 모든 모델 프로필의 설정 키에 엄격한 타입 접미사(`provider_str`, `enabled_bool`, `api_key_env_str`, `base_url_str`, `chat_completions_path_str`, `model_str`, `timeout_seconds_int`, `max_tokens_int`, `temperature_float`, `api_format_str`, `llm_id_int`, `client_env_str`, `user_env_str`, `model_path_str`, `n_ctx_int`, `n_threads_int`, `n_batch_int`, `n_gpu_layers_int`, `verbose_bool`) 적용.
  - `config_loader.py`:
    - `ReadOnlyConfig.__getattr__` 및 `__contains__`에서 접미사 유무에 따른 상호 보완 조회 지원으로 하위 호환성 및 편의성 강화.

### v0.4.46 (2026-09-09)
- **방어적 우항 껍데기 형변환(`str(...)`) 배제 및 Fail-Fast 원칙 강화 (규칙 1.3.1 및 1.5.2 준수)**:
  - `logger.py`: `ProjectLogger.__init__`에서 버그를 은폐할 수 있는 불필요한 `str(name)` 형변환 껍데기를 배제하고 `name or ""`로 순수하게 전달하여 비문자열 유입 시 조기 감지(Fail-Fast) 지원.

### v0.4.45 (2026-09-09)
- **LLM 모듈(`llm.py`) 및 로깅(`logger.py`) 엄격한 타입 접미사 표준화 및 하드코딩 제거 (규칙 1.1, 1.6.1, 1.7.5 준수)**:
  - `llm.py`:
    - 기본 설정 스키마(`APP_DEFAULT_SCHEMA_DICT`) 내 모든 설정 키에 타입 접미사(`default_provider_str`, `default_enabled_bool`, `default_timeout_seconds_int`, `default_max_tokens_int`, `default_temperature_float`, `vertex_model_str`, `gemini_model_str`, `ollama_model_str`, `ollama_endpoint_str`, `router_model_str`, `sql_generator_model_str`, `validator_model_str`)를 부여하고 소스코드 내 하드코딩 완전 배제.
    - 모듈 임포트 시 전역 설정(`config._source`)에 `APP_DEFAULT_SCHEMA_DICT`를 자동 등록하도록 개선.
    - `LlmClient` 클래스의 인스턴스 변수(`last_generated_by_str`), 메서드 인자(`purpose_str`, `prompt_str`, `system_prompt_str`, `model_name_str`, `provider_str`, `timeout_seconds_int`, `max_tokens_int`, `temperature_float`)에 엄격한 타입 접미사를 100% 적용 (기존 키워드 인자 하위 호환성 유지).
  - `logger.py`:
    - `ProjectLogger.configure`: 스키마 변경에 맞춰 타입 접미사가 적용된 설정 키(`logging.level_dict`, `logging.level_str`, `logging.format_str`, `logging.datefmt_str`, `logging.file_logging_bool`, `logging.log_file_str`)를 1차 조회하고 기존 레거시 키를 자동 폴백하도록 개선.
  - `README.md`: 한국어 및 영문 `LlmClient` 사용법 예제 코드 내 인자 명칭(`purpose_str`, `prompt_str`, `system_prompt_str`, `last_generated_by_str`) 동기화.

### v0.4.44 (2026-09-09)
- **전 모듈 내 미접미사 별칭 상수/변수 바인딩 전면 삭제 및 타입 접미사 식별자로 단일화**:
  - `llm.py`: 미접미사 별칭 변수 `_LOCAL_LLMS = _LOCAL_LLMS_DICT` 및 `APP_DEFAULT_SCHEMA = APP_DEFAULT_SCHEMA_DICT` 삭제, 모델 캐시 참조부를 `_LOCAL_LLMS_DICT`로 일원화.
  - `config_loader.py`, `logger.py`, `tool_parser.py`: 각 모듈 레벨 `APP_DEFAULT_SCHEMA = APP_DEFAULT_SCHEMA_DICT` 별칭 삭제 및 `logger.__all__` 정비.
  - `date_time_utils.py`: `FORMAT_DATE_YYYYMMDD`, `FORMAT_DATETIME_STD`, `FORMAT_DATETIME_NO_TZ`, `FORMAT_DATETIME_KST`, `FORMAT_DATETIME_COMPACT` 등 5종의 미접미사 클래스 상수 별칭 전면 삭제, 내부 및 외부 호출부(`logger.py`, `tool_parser.py`, `utils.py`)를 `_STR` 접미사 상수로 100% 단일화.
  - `medallion/tool/code/date_check_to_code.py`: 레거시 별칭 함수 바인딩(`date_check`, `evaluate_date_status`) 삭제.

### v0.4.43 (2026-09-09)
- **클라이언트 모듈(`clients.py`) 내 전 함수/메서드 지역 변수 및 인자 타입 접미사 전면 표준화 (규칙 1.6.1 및 1.6.2 엄격 준수)**:
  - `BigQueryClient.insert_rows_json_data`: `table_target` -> `table_target_any`, `rows_to_insert` -> `rows_to_insert_list`, `errors` -> `insert_errors_list`, `err_details` -> `error_details_list`, `idx` -> `row_index_int`, `e`/`loc`/`rsn` -> `single_error_dict`, `location_str`, `reason_str`, `combined_err_msg` -> `combined_error_message_str`, `clean_insert_err` -> `clean_insert_error_str` 적용.
  - `BigQueryClient.load_table_from_json_data`: `table_target` -> `table_target_any`, `rows_to_insert` -> `rows_to_insert_list`, `write_disp` -> `write_disposition_effective_str`, `job_config` -> `job_config_obj`, `load_job` -> `load_job_obj`, `sub_err_list`/`s_err`/`loc` -> `sub_error_list`, `sub_error_item_dict`, `location_str`, `clean_err` -> `clean_error_str` 적용.
  - `BigQueryClient.query`, `get_existing_keys`, `merge_table_from_json_data`: `query_job` -> `query_job_obj`, `results` -> `query_results_obj`, `job_config` -> `job_config_obj`, `p_job` -> `post_job_obj`, `clean_err_str` -> `clean_error_str` 적용.
  - `BigQueryClient.convert_to_bigquery_timestamp`: `tz_pattern` -> `tz_pattern_str`, `tz_match` -> `tz_match_obj`, `tz_suffix` -> `tz_suffix_str`, `raw_tz` -> `raw_tz_str`, `dt_part` -> `datetime_part_str` 적용.
  - `S3Client`, `GcsClient`: `paginator` -> `paginator_obj`, `pages` -> `pages_iterable`, `page`/`obj` -> `page_dict`/`object_item_dict`, `response` -> `response_dict`, `blob` -> `blob_obj`, `resolved_stream` -> `resolved_stream_any` 등 전면 개편.
  - 모듈 레벨 지연 로딩 캐시 변수: `_boto3_module`, `_boto_config_cls`, `_storage_module`, `_bigquery_module`, `_service_account_module`로 명확화.

### v0.4.42 (2026-09-09)
- **클라이언트 모듈(`clients.py`) 내 중복 비접미사 별칭 변수 전면 삭제 및 규칙 1.6.1 엄격 준수**:
  - `BigQueryClient`: 중복 할당되던 비접미사 인스턴스 변수(`self.project_id`, `self.dataset_id`, `self.table_id`, `self.credentials_path`, `self.timeout_seconds`, `self.ignore_unknown_values`, `self.timezone_offset`) 및 미사용 내부 플래그(`self._use_streaming_only`) 전면 삭제.
  - `S3Client`, `GcsClient`: 기존 중복 비접미사 인스턴스 변수(`self.endpoint_url`, `self.access_key`, `self.secret_key`, `self.bucket_name`, `self.credentials_path`, `self.timeout_seconds`) 전면 정리.
  - `clients.py` 상단 미사용 모듈 레벨 `APP_DEFAULT_SCHEMA` 별칭 제거 (선언부 단일화).
  - 상위 애플리케이션(`app/`): `ecs_to_bigquery.py`, `ecs_to_gcs.py`, `ecs_to_gcsbigquery_merge.py`, `table_transformer.py`의 클라이언트 속성 접근부를 엄격한 타입 접미사 필드(`dataset_id_str`, `table_id_str`, `project_id_str`, `bucket_name_str`)로 100% 동기화.

### v0.4.41 (2026-09-09)
- **클라이언트 모듈(`clients.py`) 엄격한 타입 접미사(`_int`, `_str`, `_bool`) 전면 복원 및 불필요한 껍데기 형변환(`bool()`, `int()`, `str()`) 제거**:
  - `clients.py` 기본 스키마(`APP_DEFAULT_SCHEMA_DICT`)의 모든 설정 키에 규칙 1.6.1에 부합하도록 타입 접미사(`timeout_seconds_int`, `chunk_size_int`, `ignore_unknown_values_bool`, `timezone_offset_str`, `max_retries_int`)를 복원.
  - `BigQueryClient`, `GcsClient`: 생성자 파라미터, 인스턴스 변수 및 메서드 인자에 타입 접미사(`_str`, `_int`, `_bool`)를 전면 표준화하고 기존 외부 호출부 호환성을 위한 프로퍼티 및 키워드 인자(`**kwargs`) 지원.
  - `ReadOnlyConfig`의 자동 타입 보증 기능(`coerce_type_by_key_suffix`)을 활용하여 불필요한 수동 중복 껍데기 형변환(`bool()`, `int()`, `str()`)을 배제하고 직접 속성 접근으로 단일화.

### v0.4.40 (2026-09-09)
- **추측성 키 접미사(`suffixes`) 자동 매칭/우회 방어 로직 전면 제거 및 1:1 엄격 일치(Fail-Fast) 원칙 확립**:
  - `ReadOnlyConfig.__getattr__`: 호출자 속성명과 설정 파일 키 간 접미사(`_str`, `_int` 등)를 자동 보완/제거하던 `suffixes` 순회 추측 로직을 전면 제거하고 미정의 키에 대해 즉시 `AttributeError`를 발생시키도록 단순화.
  - `ReadOnlyConfig.__contains__`: 접미사 유연 매칭을 배제하고 `key_str in data`로 엄격한 1:1 존재 여부 검사로 단일화.
  - `ConfigLoader.ensure_config_file`: 설정 파일 자동 복원(Self-healing) 시 접미사 유사 키를 추측 비교하던 로직을 제거하고 스키마 키와 파일 키의 완전 1:1 일치로 검증.
  - `ConfigLoader.setting`: 문자열 경로 탐색 시 접미사 임의 변환 순회를 제거하고 명시된 키 경로로만 1:1 직접 조회.
  - `app/app_schema.py`: 상위 애플리케이션 스키마의 모든 키를 `config/config.yml`의 실제 키 명칭과 100% 1:1로 일치시켜 불필요한 자동 보정 주입 원천 차단.

### v0.4.39 (2026-09-09)
- **기본 설정 스키마(`APP_DEFAULT_SCHEMA_DICT`) 상수명 및 내부 설정 키 자료형 접미사(`_str`, `_int`, `_bool`, `_list`, `_dict`) 전면 표준화**:
  - `agent_common` 전 모듈(`clients`, `logger`, `config_loader`, `llm`, `tool_parser`)의 스키마 딕셔너리 상수명을 규정 1.6.1에 맞춰 `APP_DEFAULT_SCHEMA_DICT`로 선언하고 하위 호환성 별칭(`APP_DEFAULT_SCHEMA`)을 제공.
  - `DateTimeUtils`의 시간/날짜 포맷 상수명에 `_STR` 접미사(`FORMAT_DATE_YYYYMMDD_STR`, `FORMAT_DATETIME_STD_STR` 등) 적용.
  - `ConfigLoader`: `__init__`에서 패키지 스키마를 강제 등록하여 애플리케이션 `config.yml`에 불필요한 섹션이 자동 주입되던 현상을 원천 방지하고, 템플릿 설정 필요 시 `APP_DEFAULT_SCHEMA_DICT`에서 투명하게 폴백 조회하도록 개선.
  - 상위 애플리케이션 스키마(`app/app_schema.py`): `_BASE_*_SCHEMA_DICT` 및 `ECS_TO_*_SCHEMA_DICT`의 모든 키(`prefix_str`, `target_folders_list`, `date_prefix_str`, `path_regex_str`, `table_id_str`, `max_retries_int`, `chunk_size_int`, `timeout_seconds_int` 등)에 엄격한 타입 접미사 일괄 부여.

### v0.4.38 (2026-09-09)
- **추측성·방어적 코드 전면 제거 및 불변 전역 설정 객체(`config`) 직접 속성 접근 표준화**:
  - `ToolParser`: 하드코딩 기본값(`"medallion/tool"`)과 디렉토리 추측 탐색 목록(`cand_dirs_list = [...]`)을 전면 제거하고, `config.transfer.tool_dir_str`을 통해 선언된 단일 표준 경로만 직접 조회하도록 일원화.
  - `BigQueryClient`: 코드 내부 하드코딩 fallback(`setting(..., True)`, `setting(..., "+09:00")`) 및 방어적 `getattr(self, "timezone_offset_str", "+09:00")` 코드를 제거하고 `config.bigquery.ignore_unknown_values`, `config.bigquery.timezone_offset` 직접 접근으로 전환.
  - `LlmClient`: `prompts.* or llm.*` 식의 추측성 설정 조회 체인을 전면 폐기하고 `config.llm.system_prompt_str`, `config.llm.router_model_str`, `config.llm.sql_generator_model_str`로 직관적 단일화.
  - `ProjectLogger`: `loader.setting()` 호출 시 소스코드 내 불필요하게 중복 지정되던 하드코딩 기본값 매개변수 전면 제거.
  - `ConfigLoader.ensure_config_file`: `setting("templates.config_notice_header")` 및 `setting("templates.config_repair_inline_comment")`의 하드코딩 fallback 문자열 제거.
  - 상위 애플리케이션(`app/`): `getattr(config.transfer, "save_error_json_bool", False)` 등 불필요한 방어 코드를 `config.transfer.save_error_json_bool` 직접 접근으로 정비.

### v0.4.37 (2026-09-09)
- **라이브러리 모듈 독립성 및 지연 로딩(Lazy Loading) 보장을 위한 패키지 통합 스키마(`default_schema.py`) 폐기**:
  - `agent_common`의 경량 모듈화 철학(필요한 기능만 선택적 사용)에 따라, 사용하지 않는 컴포넌트까지 일괄 결합하던 패키지 단위 통합 스키마(`default_schema.py`) 및 최상위 `APP_DEFAULT_SCHEMA`/`AGENT_COMMON_DEFAULT_SCHEMA` export를 전면 제거.
  - 사용자가 필요한 모듈(`logger`, `clients`, `config_loader` 등)만 가볍게 독립적으로 활용할 수 있도록 모듈별 스키마 자율성을 보장하고 불필요한 결합도를 제거.
  - 아키텍처 규정(1.7.5) 개정: 공통 라이브러리 패키지는 각 모듈별 기본 스키마를 독립 선언하며 패키지 통합 스키마 강제 합성을 금지함.

### v0.4.36 (2026-09-08)
- **로거 이름(`%(name)s`)의 프로그램명 통일 및 스택 프레임 기반 호출자(`%(caller)s`, `%(className)s`) 자동 분리 추출**:
  - 엔터프라이즈 분산 모니터링 및 중앙 로그 수집(Cloud Logging, BigQuery 등) 환경에 최적화하여, 로거 이름(`name`)에는 프로그램/배치 애플리케이션 명칭(`ProjectLogger.configure(app_name_str=...)`)이 일관되게 바인딩되도록 개선.
  - 로그 호출 지점의 파이썬 실행 스택 프레임(Stack Frame)을 역추적하여, 클래스 메서드 내부에서 호출 시 `self.__class__.__name__`을 자동 감지하여 `caller`(`ClassName.method()`) 및 `className` 속성을 100% 자동으로 보정.
  - 클래스 밖 모듈 일반 함수 또는 스크립트 진입점(`main()`, `run_pipeline()` 등)에서 호출 시에는 점(`.`) 없이 함수명만(`function()`) 깔끔하게 표기되도록 지원.
  - 기본 로그 포맷을 `[%(asctime)s][%(levelname)s][%(name)s][%(filename)s:%(lineno)d %(caller)s] %(message)s`로 표준화.

### v0.4.35 (2026-09-08)
- **전 모듈 `APP_DEFAULT_SCHEMA` 도입 및 선언적 설정 스키마 표준화**:
  - main 진입점이 없는 `agent_common` 라이브러리의 아키텍처에 맞춰 각 소스 파일(모듈: `logger`, `config_loader`, `clients`, `tool_parser`, `llm`)별로 사용하는 모든 기본 설정·상수를 `APP_DEFAULT_SCHEMA` 상수로 선언.
  - 각 모듈 스키마를 합성하는 `default_schema.py` 신설 및 최상위 패키지(`agent_common`) 레벨에서 `APP_DEFAULT_SCHEMA`와 `AGENT_COMMON_DEFAULT_SCHEMA`를 노출, `ConfigLoader` 기본 등록 연동.
- **주관적 로그 파일 분기(`out_file` vs `debug_file`) 폐기 및 `{log_level}` 기반 `log_file` 단일화**:
  - 모호한 약식 명칭이었던 `out_file`과 `debug_file` 이원화 체계를 전면 폐기하고, 단일 표준 경로 템플릿 `logging.log_file`로 통합.
  - 경로 템플릿 내 `{log_level}`(소문자) 및 `{LOG_LEVEL}`(대문자) 동적 치환 태그를 지원하여, 프로세스 실행 로그 레벨에 부합하는 디렉터리를 자동으로 생성하고 로그 파일을 격리 보관하도록 개선.
  - 기존 설정 파일과의 100% 하위 호환성을 위해 `log_file` 미정의 시 레거시 키(`out_file`, `debug_file`, `file`) fallback 지원 유지.
- **약식/축약 식별자 엄격 금지 및 상세·구체적 명명 원칙 준수 (AGENTS 규정 1.6.2 & 1.7.5 반영)**:
  - `logger.py` 내부의 약식 변수명(`out_file`, `debug_file`, `log_file` 등)을 `output_error_log_file_str`, `debug_log_file_str`, `default_log_file_str`, `target_log_file_path_str`, `file_logging_enabled_bool` 등으로 전면 정비.
  - 모호한 약식 명칭으로 인해 설정/변수가 누락된 것으로 오인하고 중복 키를 재작성하는 혼선과 오류 원천 차단.

### v0.4.34 (2026-09-08)
- **AWS S3 및 Dell ECS 범용 클라이언트 `S3Client` 신설 및 `EcsClient` 하위 호환 보장**:
  - 기존 Dell ECS 전용으로 명명된 `EcsClient`를 AWS S3 및 Dell ECS(S3 호환 스토리지) 모두를 유연하게 지원하는 범용 클라이언트 `S3Client`로 전면 개편.
  - `endpoint_url_str`을 선택적(Optional)으로 변경하여, 미지정(`None`) 시 AWS 기본 S3 엔드포인트로 자동 접속되고, 값 지정 시 온프레미스 Dell ECS 또는 MinIO 등으로 즉시 접속되도록 개선.
  - AWS 환경에서의 Signature V4 서명을 위한 `region_name_str` 파라미터 신설.
  - AWS IAM Role / 인스턴스 프로파일 자격 증명 자동 탐색을 지원하기 위해 `access_key_str` 및 `secret_key_str` 생략 가능하도록 유연화.
  - 기존 코드의 중단 없는 실행을 위해 `EcsClient = S3Client` 모듈 레벨 별칭(Alias) 제공 및 레거시 키워드 매개변수(`endpoint_url`, `access_key`, `secret_key`, `bucket_name`, `timeout_seconds`, `ecs_key`, `size` 등) 100% 하위 호환 지원.
- **선택적 의존성에 `s3` extras 추가**:
  - `pyproject.toml`의 `[project.optional-dependencies]`에 `s3 = ["boto3>=1.26.0"]` 추가 (기존 `ecs` 옵션 병행 유지).

### v0.4.33 (2026-09-07)
- **클라우드 스토리지 SDK 지연 로딩(Lazy Loading) 및 패키지 초경량화**:
  - `EcsClient`, `GcsClient`, `BigQueryClient` 구동에 필요한 무거운 서드파티 SDK(`boto3`, `google-cloud-storage`, `google-cloud-bigquery`)를 모듈 임포트 시점이 아닌 클라이언트 연결(`_connect`) 및 쿼리 실행 시점에 동적 로드하도록 구조 개선.
  - 외부 SDK 미설치 상태에서도 `agent_common` 최상위 패키지 및 `clients` 모듈을 에러 없이 안전하게 import 가능하도록 보장.
  - 해당 클라이언트 구동 시 라이브러리가 설치되어 있지 않을 경우 설치 명령어(`pip install boto3` 등)를 상세 안내하는 명확한 `ImportError` 예외 발생.
  - 타입 체커 및 IDE 정적 분석 지원을 위해 `TYPE_CHECKING` 블록을 유지하여 개발 생산성 보장.
- **선택적 의존성(Optional Dependencies / Extras) 분리**:
  - `pyproject.toml`의 기본 `dependencies`에서 무거운 클라우드 SDK를 전면 분리하고, 필요한 환경에 따라 선택 설치할 수 있도록 `[project.optional-dependencies]` (`clients`, `ecs`, `gcp`, `all`) 신설.
  - 기본 설치(`pip install agent_common`) 시 `PyYAML`만 설치되는 초경량 풋프린트 달성.
- **불필요한 `requests` 의존성 전면 제거**:
  - 패키지 내 모든 HTTP 통신이 파이썬 표준 라이브러리(`urllib.request`)로 구현되어 있으므로, 미사용 서드파티 라이브러리인 `requests`를 의존성 목록에서 완전 삭제(AGENTS.md 규칙 1.2.1 보안 취약점 최소화 준수).

### v0.4.32 (2026-09-06)
- **타입 접미사 자동 변환 함수의 공개 모듈 레벨 승격 및 범용화 (`coerce_type_by_key_suffix`)**:
  - `ReadOnlyConfig` 내부의 비공개 정적 메서드(`_coerce_type_by_key_suffix`)를 패키지 최상위 모듈 공개 함수 `coerce_type_by_key_suffix(key_str, val_any)`로 승격.
  - `config.yml` 뿐만 아니라 임의의 YAML, JSON, 데이터 사전(Dict) 및 비즈니스 파이프라인에서 단독 함수로 즉시 import하여 활용 가능하도록 개방.
  - 기존 클래스 정적 메서드(`ReadOnlyConfig.coerce_type_by_key_suffix` 및 `_coerce_type_by_key_suffix`)와의 100% 하위 호환성 유지.
- **타입 변환 실패 시 조용한 침묵 실패(Silent Failure) 제거 및 엄격한 Fast-Fail 정책 준수**:
  - 기존에 `int(val_any)` 또는 `float(val_any)` 변환 실패 시 원본 문자열을 그대로 반환하던 안티패턴을 전면 제거.
  - 소스코드 내 하드코딩된 예외 문자열 조립을 배제(No Hardcoding & DRY 준수)하고, `logging_messages_*.yml`에 단일화된 전용 로그 ID(`config_type_coercion_failed`) 템플릿을 구축하여 불필요한 메시지 중복을 전면 제거.
  - `_raise_coercion_error` 공통 헬퍼를 통해 `logger.exception("config_type_coercion_failed", ...)`를 호출하여 원천 Traceback과 에러 텔레메트리 카운트를 기록한 뒤, 상세 안내 메시지와 함께 Fast-Fail 예외(`ValueError` / `TypeError`)를 발생시키도록 설계 개선.
- **중첩 딕셔너리 일괄 재귀 타입 보증 헬퍼 함수 신설 (`coerce_dict_by_key_suffix`)**:
  - 다중 계층으로 구성된 외부 설정 파일(YAML/JSON) 전체를 단 한 줄로 일괄 정제할 수 있도록, 딕셔너리 및 하위 리스트를 재귀 순회하며 접미사 규칙을 자동 변환하는 `coerce_dict_by_key_suffix(data_dict)` 함수 신설.
- **`ReadOnlyConfig`의 다중 설정 파일 지원 확장 (설정 소스명 매개변수화)**:
  - `ReadOnlyConfig(data, source_name_str="config.yml")` 형태로 인스턴스화 시 설정 파일명/소스명을 지정할 수 있도록 확장.
  - 임의의 외부 설정 파일(`rule.yml`, `mapping.yml` 등)을 래핑했을 때 키 누락 시 해당 파일명(예: `rule.yml에 정의되지 않은 설정 항목입니다`)으로 정확한 `AttributeError` 메시지 출력 지원.
- **`agent_common` 최상위 패키지 export 및 `__all__` 등록**:
  - `from agent_common import coerce_type_by_key_suffix, coerce_dict_by_key_suffix` 지원.

### v0.4.31 (2026-09-04)
- **공개 배포 규격 준수를 위한 로깅 매뉴얼 내 사설·폐쇄망 식별자 전면 비식별화 및 일반화**:
  - `manual/kr/logger/` 및 `manual/en/logger/` 전반에 걸쳐 사내 폐쇄망 자산 및 스크립트 식별자, 내부 로그 디렉터리 경로를 표준 엔터프라이즈 가상 데이터 파이프라인 규격(`data_extractor`, `stream_processor`, `db_loader`, `logs/pipeline/...`, `Cloud_Data_Sync`)으로 전면 변형 및 비식별화.
- **`02_project_logger_configure.md` 로그 레벨별 동적 라우팅 및 템플릿 실전 예시 보강**:
  - `logging.level` 설정값에 따라 장애 격리 저장용 `out_file`과 상세 추적용 `debug_file`로 분기되는 동작 메커니즘을 엔터프라이즈 파이프라인 실전 예제로 구체화.
  - `{app_name}` 및 `%Y/%m/%d/%Y%m%dT%H%M%S` 동적 템플릿 경로 해석 및 생성 검증 예시 보강.
- **Mermaid 아키텍처 다이어그램 GitHub 렌더링 호환성 개선**:
  - GitHub 렌더러 파싱 오류를 방지하기 위해 노드 라벨 내 괄호 및 특수문자 큰따옴표 감싸기(`["..."]`) 및 엣지 라벨 표준 구문(`-->|"..."|`)을 한국어/영어 매뉴얼 10종에 전면 적용.
- **로깅 결과 추적 식별자 소문자 `snake_case` 표준화**:
  - `04_execution_result_and_error_tracking.md` 및 `05_summary_report_generation.md` 내 에러/제외 로그 ID를 소문자 `snake_case` 표준으로 정제.
- **`llm.py` 내 `Path` 타입 힌트 누락 import(`from pathlib import Path`) 추가**:
  - `LlmClient.__init__`의 `config_dir: str | Path | None` 인자 타입 힌팅 해석 및 런타임 검증 시 발생할 수 있는 잠재적 NameError 해소.

### v0.4.30 (2026-09-04)
- **`agent_common.logger` 모듈의 5대 주요 기능별 상세 기술 매뉴얼(한국어/영어 총 10종) 신설 및 README 연동**:
  - `manual/kr/logger/` 및 `manual/en/logger/` 디렉터리에 로깅 포매터 및 로거의 핵심 기능 5종에 대한 심층 기술 문서(아키텍처 다이어그램, 메커니즘, 실전 코드 예시, 운영 베스트 프랙티스) 작성:
    1. `01_single_line_flatten_formatter.md`: `SingleLineFlattenFormatter`, `[Origin: ...]` 프레임 추출 및 단일 행 평탄화, 중앙 로그 수집기(Logstash, Fluentd 등) 연동 최적화
    2. `02_project_logger_configure.md`: `ProjectLogger.configure()`, 콘솔/파일 핸들러 분기, 일자별 디렉터리, 레벨별 파일 분리(`out_file`, `debug_file`), 서드파티 노이즈 억제
    3. `03_multilingual_message_catalog.md`: `logging_messages_ko.yml`/`en.yml`, 런타임 동적 언어 전환(`set_language`), `safe_kwargs` 템플릿 치환, 프로젝트별 메시지 사전 확장 실전 가이드
    4. `04_execution_result_and_error_tracking.md`: 성공/실패/제외(Skip) 3단계 상태 분류, 인스턴스 및 클래스 전역 멀티스레드 집계, 소문자 `snake_case` 로그 식별자 표준화
    5. `05_summary_report_generation.md`: `ProjectLogger.log_summary()`, 80열 표준 요약 블록, 처리 속도(items/s), 전송률(MB/s), 에러/제외 사유 직관적 한글/영문 자동 해석(`get_log_id_description`), `ProgressTracker` 연동
- **`README.md` 내 기능 설명 및 상세 기능 매뉴얼(User Manuals) 테이블에 2.1~2.5 링크 추가**:
  - 한국어 및 영문 섹션 2와 상세 매뉴얼 테이블에 신규 매뉴얼 5종의 바로가기 링크와 핵심 요약 반영.

### v0.4.29 (2026-09-04)
- **`pyproject.toml` 패키지 설명(`description`) 전면 개편 및 다국어 병기**:
  - 패키지 발전 방향 및 현재 핵심 기능(설정, 구조화 로깅, 도구 파싱, 진행률 추적)에 부합하도록 한글 설명을 전면 개편하고 영문 설명을 병기 (`자율 에이전트 및 데이터 파이프라인을 위한 경량 설정·로깅·도구 프레임워크 (Lightweight configuration, logging, and tooling framework for autonomous agents and data pipelines)`).

### v0.4.28 (2026-09-04)
- **`llmpool.yml` 및 `llm.py` 내 사내 GenAI 허브 엔드포인트 도메인 비식별화 및 보안 정제**:
  - `src/agent_common/config/llmpool.yml` 내 사내 전용 클라우드 도메인 및 엔드포인트 URL을 표준 가상 엔드포인트(`https://genaihub.example.com/v1/messages`)로 비식별화.
  - `src/agent_common/llm.py`의 `_generate_fabrix` 메서드 Docstring 내 사내 도메인 식별자 제거.

### v0.4.27 (2026-09-04)
- **공개 배포를 위한 폐쇄망·사설 식별자 전면 비식별화 및 설계자 소속 정보 제거**:
  - 공개 저장소(GitHub / PyPI) 배포 규격에 맞추어 사내 폐쇄망 자산 식별자, 내부 IP, 전용 테이블 ID, 내부 스토리지 경로를 가상의 표준 예제 규격(API/배치/스트리밍 등)으로 전면 정제.
  - 소스코드 및 문서 헤더에서 설계자 소속 정보 및 사내 도메인 이메일을 전면 제거하고 개인 개발자 서식으로 일원화.
- **`manual/kr/config_loader/06_ensure_config_self_healing.md` 및 영문 문서 핵심 철학 전면 보강**:
  - `ensure_config_file`의 본질적 주 목적을 '코드 내 모든 상수의 설정 파일화(외부화) 및 가시화'로 명문화하고, 자가 치유(Self-healing)는 이를 구현하는 부수적 메커니즘임을 명시.
  - 코드 맨 처음/최초 기동단(Entry Point)에서의 기본 스키마(`default_schema`) 정의 및 누락 상수 강제 주입(In-place injection) 패턴 가이드 전면 보강.
  - 다중 프로그램 환경에서의 공통 상수 공유 및 스키마 합성 패턴(`app_schema.py`) 신설 (복수의 CLI 프로그램이 단일 `config.yml`과 인프라 상수를 공유하면서 프로그램별 고유 옵션을 DRY 원칙에 따라 조합하는 실전 아키텍처 가이드 추가).
  - 상수의 분산 정의 및 코드 중간 하드코딩 안티패턴 경고 추가 (스키마 외부에 상수를 따로 정의하거나 코드 중간에 선언하면 본 기능이 무의미해짐을 명시).
  - Mermaid 상수 강제 주입 흐름도 갱신 및 `README.md` 매뉴얼 설명/계층 번호 체계(`1.1` ~ `1.6`) 최적화.

### v0.4.26 (2026-09-04)
- **`manual/kr/config_loader/02_readonly_dot_notation.md` 및 영문 문서 보강**:
  - 실제 `config/config.yml` 전체 예제 스키마 및 파이썬 점 표기법 1:1 매핑 가이드 추가.
  - 기본 경로(`config/config.yml`) 외 다른 사용자 정의 경로(`config_dir`) 지정 및 동적 경로 변경, 테스트용 인메모리 딕셔너리 전달 3가지 실전 패턴 가이드 신설.
- **PyPI 설명 연동을 위한 README 매뉴얼 링크 GitHub 절대 경로 전환**:
  - PyPI 패키지 페이지에서 매뉴얼 링크가 깨지지 않고 바로 열리도록 한국어/영어 12종 매뉴얼 링크를 GitHub 저장소 절대 URL(`https://github.com/...`)로 전환.

### v0.4.25 (2026-09-04)
- **`config_loader` 주요 6대 기능별 상세 기술 매뉴얼(한국어/영어 총 12종) 신설 및 README/PyPI 연동**:
  - `manual/kr/config_loader/` 및 `manual/en/config_loader/` 디렉터리에 `agent_common.config_loader`의 핵심 기능 6종에 대한 심층 기술 문서(아키텍처, 알고리즘, 실전 코드 예시) 작성:
    1. `01_hierarchical_yaml_merge.md`: 5단계 계층 병합 순서, `_deep_merge` 재귀 알고리즘, 프로젝트 루트 3중 자동 감지
    2. `02_readonly_dot_notation.md`: 불변 점 표기법 조회(`ReadOnlyConfig`), 런타임 설정 변조 차단(Read-Only), 딕셔너리 호환성
    3. `03_type_coercion_and_guarantee.md`: 타입 접미사(`_int`, `_float`, `_bool`, `_str`, `_list`, `_dict`) 자동 캐스팅 및 타입 안전성 보증
    4. `04_fail_fast_require_setting.md`: `require_setting` 기반 기동 초기 필수 설정 검증, 상세 진단 로그 및 Fail-Fast 안전 조기 종료
    5. `05_network_proxy_control.md`: `proxy.no_proxy` 설정의 OS `NO_PROXY` 환경변수 자동 반영 및 내부망 프록시 우회
    6. `06_ensure_config_self_healing.md`: 코드 내 모든 상수의 설정 파일화(외부화), `ensure_config_file`을 통한 `config.yml` 자동 생성 및 누락 상수 강제 주입·보정
  - `README.md` 내 각 불릿 항목에 매뉴얼 직접 링크 연결 및 한국어/영문 `### 📖 상세 기능 매뉴얼 (User Manuals)` 요약 테이블 신설.
  - `MANIFEST.in`에 `graft manual` 및 `recursive-include manual *.md`를 추가하여 소스 배포판(`sdist`) 내 매뉴얼 아카이빙 지원.
  - `pyproject.toml`의 `[project.urls]`에 `Manual (Korean)` 및 `Manual (English)` GitHub 경로 등록.

### v0.4.24 (2026-09-04)
- **다국어 로그 메시지 템플릿 사전(`logging_messages_en.yml`) 및 설정 기반 언어 선택(`logging.language`) 지원**:
  - 영문 로그 메시지 템플릿 사전(`src/agent_common/config/logging_messages_en.yml`)을 신규 제작하여 모든 로그 레벨(`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) 및 도메인 메시지의 자연스럽고 전문적인 영문 템플릿 제공.
  - 기존 `logging_messages.yml`을 `logging_messages_ko.yml`로 정비하여 한국어/영문 사전 체계를 명확히 분리.
  - `config.yml`의 `logging.language`(또는 `logging.lang`) 옵션을 통해 `"KO"`(한국어, 기본값) 또는 `"EN"`(영어, 대소문자 무관)을 자유롭게 선택하여 사용할 수 있도록 `ConfigLoader` 로직 개편.
  - `ConfigLoader.set_language()` 및 `ProjectLogger.set_language()` 메서드/프로퍼티를 지원하여 런타임 동적 언어 전환 지원.
  - 개별 프로젝트의 고유 템플릿 사전(`config/logging_messages_en.yml`, `config/logging_messages_ko.yml`, `config/logging_messages.yml`) 오버라이드 병합 연동 완벽 보장.
- **`ProjectLogger` 처리 제외(Skip) 로그 ID 기반 상세 내역 집계 및 요약 리포트(`log_summary`) 고도화**:
  - `ProjectLogger`에 제외 식별자(로그 ID)별 발생 건수를 누적하는 `record_exclusion()`, `get_excluded_counts()`, `reset_excluded_counts()` 및 클래스 전역 집계(`_excluded_counts_dict`) 메서드 추가.
  - `record_excluded(log_id_or_count, count_int)` 및 `update(..., log_id_str)`를 개선하여 제외 로그 ID 인자 전달 시 내부 제외 딕셔너리에 자동 분기 집계 지원 (기존 호출부와 100% 하위 호환).
  - 모듈 간(예: `TableDataTransformer` -> `EcsToBigquery`) 멀티 로거 인스턴스 환경에서도 누락 없이 통합 집계되도록 `get_error_counts()` 및 `get_excluded_counts()`의 전역 집계 우선 반환 로직 정돈.
  - 최종 실행 요약 리포트(`log_summary`)에 `- 처리 제외 세부 내역 (총 N건):` 블록을 추가하여, `logging_messages_*.yml` 메시지 템플릿으로부터 요약 설명을 동적으로 추출하여 `* 로그ID (설명): N 건` 형식으로 상세 출력 지원.
  - `ProgressTracker.log_summary()`에 `excluded_counts_dict`, `error_counts_dict` 파라미터 전달 연동 지원.

### v0.4.23 (2026-09-03)
- **README 및 CHANGELOG 한/영 이원화(다국어 지원) 및 GitHub 연동**:
  - `README.md` 상단에 한국어/영문 점프 앵커 링크([ 🇰🇷 한국어 ] / [ 🇺🇸 English ])를 도입하여 PyPI 및 GitHub 가독성 개선.
  - 영문 버전 문서화 대칭 구성 및 영문 전용 변경 이력(`CHANGELOG_EN.md`) 신설.
  - PyPI 설명란 내 상대 경로로 깨지던 `CHANGELOG.md` 링크를 공식 GitHub 원격 저장소 링크로 수정.
  - `pyproject.toml` 내 `project.urls`(Repository, Changelog) 메타데이터 등록 및 배포 패키지(`MANIFEST.in`) 동기화.

### v0.4.22 (2026-09-03)
- **PyPI 공공 배포를 위한 표준 `src` 레이아웃 전환 및 패키지 용량 최적화**:
  - 패키지 소스 코드(`*.py`) 및 리소스(`config/`, `schemas/`, `tool/`)를 `src/agent_common/` 표준 하위 구조로 격리 배치.
  - `pyproject.toml` 설정을 `[tool.setuptools.packages.find] where = ["src"]` 표준 자동 탐색 방식으로 전환.
  - `MANIFEST.in` 최신화 및 `whls/`, `dist/`, `build/` 등 대용량 아티팩트의 배포 아카이브 유입 원천 차단(prune) 적용.
  - 불필요한 바이너리/의존성 파일 배제(약 수십 MB -> 수십 KB 수준)로 PyPI 공공 배포 안정성 및 설치 경량화 달성.

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
  - `ToolParser` 클래스 신설: 이원화된 도구 계층(1순위: 내장 `agent_common/tool`, 2순위: 로컬 `app/tool`) 동적 로드 및 `{ }` 템플릿 구문 치환/평가 엔진 제공.
  - `agent_common/tool/date/` 내장 범용 도구 신설: `DateTimeUtils`, `get_now_compact` (14자리 일시), `get_today` (8자리 일자), `get_now_formatted` (포맷팅 일시).
  - 시스템 표준 네임스페이스 `sys` 확장 및 공통 스키마(`agent_common/schemas/sys.json`) 탑재: `{sys.now_compact}`, `{sys.timestamp_compact}` (14자리 일시) 기본 제공.
  - `agent_common` 최상위 패키지에서 `ToolParser` 노출 (`from agent_common import ToolParser`).

### v0.3.80 (2026-08-21)
- **소스 코드 헤더 설계자(김유상) 명칭 정정 및 표준화**:
  - 모든 모듈 파일 헤더 내 저작권 및 설계자 정보 명칭을 표준 서식으로 통일 및 정정.

### v0.3.79 (2026-08-21)
- **`BigQueryClient` 범용 SELECT 쿼리 메서드(`query`) 신설**:
  - 임의의 SQL 쿼리를 실행하여 결과 행들을 `list[dict[str, Any]]` 형태로 반환하는 범용 `query()` 메서드 추가 (공통 코드 테이블 실시간 조회 등 지원).

### v0.3.78 (2026-08-20)
- **`BigQueryClient` 입력 데이터(JSON dict/list) 정규화 및 분기 로직 간소화**:
  - `load_table_from_json_data`, `insert_rows_json_data`, `merge_table_from_json_data` 내 중복 `if/elif` 분기 처리를 한 줄 조건식 정규화로 개선하여 가독성 향상.

### v0.3.77 (2026-08-20)
- **BigQuery 적재 시 삭제 상태 자산(`asstStusCd == '09'`) 능동적 필터링 및 로그 템플릿 추가**:
  - `logging_messages.yml` 내 `bq_deleted_asst_stus_skipped`, `bq_all_rows_deleted_asst_stus_skipped` 경고 템플릿 등록.
  - 삭제 상태코드 행을 능동적으로 선제 필터링하여 BigQuery 적재 대상에서 제외하는 로직 구현.

### v0.3.76 (2026-08-20)
- **`ProgressTracker` 유틸리티 및 배치 실시간 진행률/최종 요약 리포트 시스템 구축**:
  - `ProgressTracker` 클래스 신설: 실시간 진행률(`[N/Total] (P%)`, 성공/실패/제외 카운트, 경과시간, 전송량) 추적.
  - 진행률 레벨 차등 출력: 일반 진행률은 `INFO` 레벨로 출력하되, `config.yml`의 `logging.progress_interval_percent`(기본값: `10%`) 배수 마일스톤 및 완료 시점은 `WARNING` 레벨로 승격 출력하여 `WARNING` 운영 모드에서도 모니터링 보장.
  - 최종 결과 요약(Summary Report) 블록을 `WARNING` 레벨로 출력.
  - 메인 파이프라인 프로그램들에 `ProgressTracker` 및 Summary Report 전면 연동.

### v0.3.75 (2026-08-20)
- **로그 파일 생성 활성화/비활성화 제어 옵션(`logging.file_logging` 및 CLI `--file-log`/`--no-file-log`) 지원**:
  - `config.yml` 내 `logging.file_logging` (기본값: `true`) 설정 항목 추가.
  - `ProjectLogger.configure`에 `file_logging` 파라미터를 추가하여 파일 로깅 활성화 여부를 동적으로 제어(비활성화 시 FileHandler 생성을 건너뛰고 콘솔 출력만 유지).
  - 메인 CLI 프로그램들의 옵션에 `--file-log` 및 `--no-file-log` 플래그 추가.

### v0.3.74 (2026-08-20)
- **BigQuery TIMESTAMP 타임존 오프셋 설정(`bigquery.timezone_offset`) 및 포맷팅 지원**:
  - `config.yml` 내 `bigquery.timezone_offset` (기본값: `+09:00`) 설정 항목 추가 및 `BigQueryClient`에 바인딩.
  - `BigQueryClient.format_timestamp`에서 원천 데이터에 타임존이 없을 경우 `config.yml`의 `timezone_offset`을 자동 부여하고, 기존 타임존 오프셋(`Z`, `+09:00` 등)은 그대로 보존하도록 개선.
  - `DateTimeUtils.FORMAT_DATETIME_STD` 기본 포맷을 `%Y-%m-%d %H:%M:%S+09:00`로 일원화하여 `{sys.now}` 및 시스템 생성 타임스탬프에 KST 타임존 오프셋 명시.

### v0.3.73 (2026-08-20)
- **`ProjectLogger` 실제 호출 원천 위치(파일명, 라인 번호, 함수명) 추적 개선**:
  - `ProjectLogger` 래퍼 메서드(`info`, `warning`, `error`, `critical`, `debug`, `exception`, `log_msg`)에 `stacklevel=2`를 적용하여 어댑터 내부 위치(`logger.py:245 warning()`) 대신 실제 호출한 원천 소스코드 위치를 정확히 출력하도록 개선.

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
  - `require_setting`이 `config/` 디렉터리뿐만 아니라 프로젝트 내 임의의 상대/절대 파일 경로를 직접 지정받아 검증할 수 있도록 지원.
  - 중복 파일 검증 로직을 `require_setting`으로 일원화(SRP/DRY 준수).

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
  - 빅쿼리 테이블 룰 및 코드 정의 파일(`table_column_code.yml`, `table_rules.yml`, `table_schema.json`)의 `schemas/bigquery/` 배치 지원.

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
