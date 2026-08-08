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
