# agent_common 패키지

중앙 에이전트 및 데이터 이관/생성 서비스를 위한 공통 로깅, 설정 로더, 인프라 클라이언트, 동적 도구(Tool) 파서 및 에러 처리 라이브러리 패키지입니다.

---

## 📌 주요 제공 기능

### 1. 설정 로더 및 불변 설정 객체 (`agent_common.config_loader`)
- **계층적 YAML 설정 해석 및 병합 (Deep Merge)**: 패키지 기본 설정(`agent_common/config/*.yml`)과 개별 프로젝트 설정(`config/*.yml`) 동적 병합.
- **불변 점 표기법 조회 (`ReadOnlyConfig`)**: `config.ecs.endpoint_url`, `config.transfer.max_workers_int` 형태로 직관적 속성 접근 및 런타임 변조 방지.
- **타입 접미사 자동 형 변환 및 타입 보증 (Type Guarantee & Coercion - v0.4.14)**:
  - `_int`: `int` 정수형 자동 형 변환 및 보증
  - `_float`: `float` 실수형 자동 형 변환 및 보증
  - `_bool`: `bool` 불리언형 자동 변환 (`"true"`, `"false"`, `1`, `0` 등 완벽 대응)
  - `_str`: `str` 문자열 변환 및 `.strip()` 공백 자동 정제
  - `_list` / `_dict`: 리스트 / 불변 딕셔너리(`ReadOnlyConfig`) 래핑 보증
- **Fail-Fast 필수 설정 검증 (`require_setting()`)**: 프로그램 시작 시 필수 설정값 누락 시 상세 원인 출력 후 프로세스 즉시 종료.
- **네트워크 프록시 제어**: `proxy.no_proxy` 설정의 `NO_PROXY` 환경변수 자동 반영.
- **설정 파일 템플릿 보정 (`ensure_config_file()`)**: 프로젝트 설정 누락 시 기본 스키마 기반 자동 생성 및 자가 치유(Self-healing).

### 2. 단일 행 로깅 포매터 및 로거 (`agent_common.logger`)
- `SingleLineFlattenFormatter`: 모든 로그 및 Traceback 예외 메시지를 1줄로 평탄화하여 중앙 로그 수집(Logstash, Fluentd 등)에 최적화
- `ProjectLogger`: 콘솔 및 파일 로그 핸들러 동적 생성 및 일자별 로그 분리 관리
- `logging_messages.yml` 사전 기반 한글 포맷 템플릿 연동 로깅 지원

### 3. 스토리지 및 데이터베이스 클라이언트 (`agent_common.clients`)
- `EcsClient`: Dell ECS S3 저장소 접속, 목록 조회, 메타데이터 해석 및 파일 메모리 스트리밍 획득
- `GcsClient`: Google Cloud Storage 연결, 파일 존재 검증 및 대용량 멀티스레드 스트리밍 업로드
- `BigQueryClient`: Google Cloud BigQuery 연결, JSON 데이터 스트리밍 입력(`insert_rows_json`), 배치 로드(`load_table_from_json_data`), 인라인 MERGE(`merge_table_from_json_data`), 범용 SQL 쿼리(`query`)

### 4. 동적 도구 로더 및 템플릿 평가기 (`agent_common.tool_parser`) & 내장 도구 (`agent_common.tool`)
- **이원화된 Tool 디렉터리 계층 탐색**:
  - **1순위 (내장 도구)**: `agent_common/tool/` 하위 모듈 (전사 표준 내장 도구)
  - **2순위 (프로젝트 도구)**: `config.yml`의 `transfer.tool_dir`에 지정된 로컬 경로 (예: `medallion/tool/`)
- **선언적 템플릿 치환 및 표현식 평가 (`ToolParser.eval`)**:
  - 변수 네임스페이스 바인딩: `{ecs.key}`, `{sys.today}`, `{json.title}`
  - 동적 도구 함수 호출: `"{code.date_check_to_code(contentInfo.enddate)}"`, `"{path.get_json_name(ecs.key)}"`
  - 문자열 슬라이싱/메서드: `"{raw_key.lstrip('/')}"`, `"{raw_size|0}"`
- **안전한 네임스페이스 탐색 (`_SafeNamespace`)**:
  - 대소문자 무관 탐색 및 누락된 필드에 대해 KeyError 없이 안전하게 빈 문자열(`""`) 반환
- **내장 공통 도구 (`agent_common.tool.date.DateTimeUtils`)**:
  - `get_today_yyyymmdd()`: `YYYYMMDD` 형식 8자리 일자 반환 (예: `20260824`)
  - `get_now_compact()`: `YYYYMMDDHHMMSS` 형식 14자리 압축 일시 반환 (예: `20260824110500`)
  - `get_now_formatted(fmt)`: `YYYY-MM-DD HH:MM:SS+09:00` 표준 KST 포맷 일시 반환
- **시스템 컨텍스트 스키마 (`agent_common.schemas.sys.json`)**:
  - `{sys.today}`, `{sys.now_compact}`, `{sys.timestamp_compact}`, `{sys.env}` 등 기본 자동 제공

### 5. 진행률 트래커 및 공용 유틸리티 (`agent_common.utils`)
- `ProgressTracker`: 멀티스레드 실시간 진행률 추적(`[N/Total] (P%)`), 처리 속도 및 남은 시간 예측, 마일스톤 경고 승격 로깅, 최종 요약 리포트(Summary Report) 생성
- `DateTimeUtils`: 전역 일시 헬퍼 함수군

### 6. 공용 에러 및 예외 핸들러 (`agent_common.error_handler`)
- 네트워크 장애, 설정 오류, 런타임 예외에 대한 일관된 로깅 및 핸들링 제공

### 7. 통합 LLM 클라이언트 및 추론 엔진 (`agent_common.llm`)
- **다중 프로바이더 통합 지원 (`LlmClient`)**:
  - **외부 LLM API**: OpenAI 호환 표준 API (`/chat/completions`) 및 Fabrix 전용 API 형식 지원
  - **로컬 GGUF 모델**: `llama-cpp-python` 기반 로컬 CPU/GPU 가속 추론 및 인메모리 모델 캐싱(`_LOCAL_LLMS`)
- **설정 풀(Pool) 기반 모델 프로필 관리**:
  - `llmpool.yml` 및 `config.yml`을 통해 모델명, 토큰 수(`max_tokens`), 온도(`temperature`), 타임아웃, 컨텍스트 크기(`n_ctx`), 스레드 수(`n_threads`), GPU 레이어(`n_gpu_layers`) 등 동적 구성
- **자동 장애 복구 (Auto Failover)**:
  - `provider: auto` 설정 시 외부 LLM API 호출 실패 시 로컬 GGUF 모델로 무중단 자동 전환
- **추론 예외 통일 관리 (`LlmInferenceError`)**:
  - API 키 누락, 타임아웃, 모델 로드 실패 등에 대한 통합 예외 처리

---

## 🛠️ 사용 예시 (Usage Examples)

### 1. 전역 `config` 점 표기법 및 타입 보증 활용
```python
from agent_common.config_loader import config

# 1) 타입 접미사에 따른 자동 형 변환 보증
max_workers: int = config.transfer.max_workers_int       # int 타입 보증
prefix: str = config.gcs.prefix_str                      # str 타입 및 .strip() 정제 보증
is_ecscopy: bool = config.gcs.ecscopy_bool               # bool 타입 보증

# 2) 계층적 속성 접근
ecs_url: str = config.ecs.endpoint_url
table_id: str = config.bigquery.table_id
```

### 2. ToolParser를 통한 동적 룰 평가
```python
from agent_common.tool_parser import ToolParser

# ToolParser 인스턴스 생성 (설정 파일 기반으로 내장/로컬 Tool 자동 탐색)
tool_parser = ToolParser()

# 컨텍스트 데이터 준비
context_dict = {
    "ecs": {"key": "/unstr_data/PAK/contentInfo/orgfile/20260804/12345.html.json"},
    "contentInfo": {"enddate": "2024-12-31"},
    "sys": tool_parser.build_sys_context(),
}

# 1) 도구 함수 호출 템플릿 평가
date_code = tool_parser.eval("{code.date_check_to_code(contentInfo.enddate)}", context_dict)
# -> "09" (만료 판정)

# 2) 네임스페이스 및 내장 일시 템플릿 평가
today_val = tool_parser.eval("{sys.today}", context_dict)
# -> "20260824"
```

### 3. ProgressTracker 실시간 진행률 추적
```python
from agent_common.utils import ProgressTracker
from agent_common.logger import ProjectLogger

logger = ProjectLogger("MyTask")
tracker = ProgressTracker(total_items_int=1000, logger_obj=logger, item_name_str="파일")

for file_info in file_list:
    try:
        # 처리 로직 수행
        tracker.increment_success(bytes_int=len(data))
    except Exception as e:
        tracker.increment_failure(error_msg_str=str(e))

# 최종 결과 요약 리포트 출력
tracker.log_summary()
```

### 4. LlmClient를 통한 통합 텍스트/SQL 생성
```python
from agent_common.llm import LlmClient

# 1) 설정 풀에 정의된 모델명 또는 용도로 클라이언트 초기화
llm_client = LlmClient(purpose="sql_generator")

# 2) 프롬프트 기반 텍스트 생성 (외부 API -> 로컬 GGUF 자동 폴백)
prompt_str = "사용자 요청: 2026년 8월 일일 가입자 수 통계 쿼리를 작성해줘."
response_str = llm_client.generate(
    prompt=prompt_str,
    system_prompt="당신은 BigQuery 전문 SQL 생성 AI입니다."
)

print(f"생성된 결과 ({llm_client.last_generated_by}):\n{response_str}")
```

---

## 🚀 설치 및 빌드 방법

### 📦 Wheel 패키지 빌드 (.whl 생성)

새로운 버전으로 패키징하여 `.whl` 파일을 빌드할 경우 `scripts/build_agent_common_whl.py` 또는 `agent_common` 디렉터리 내에서 아래 명령을 실행합니다.

#### 1. 사내 폐쇄망 환경 (인터넷 차단, 완전히 오프라인 빌드)
외부 PyPI 접속을 완전히 차단하기 위해 `--no-index`, `--no-build-isolation`, `--no-deps` 옵션을 지정합니다.

```bash
# 루트 디렉터리에서 자동 빌드 스크립트 실행 (권장)
python scripts/build_agent_common_whl.py

# 또는 pip wheel 직접 실행
pip wheel ./agent_common --no-index --no-build-isolation --no-deps -w whls/
```

#### 2. 인터넷 연동망 환경 (온라인 빌드)

```bash
# pip wheel 이용
pip wheel ./agent_common --no-deps -w whls/

# 또는 build 모듈 이용
python -m build agent_common --wheel -o whls/
```

### Wheel 패키지 설치
```bash
# 개발 환경 (Editable 모드)
pip install -e agent_common

# 배포 환경 (Wheel 패키지 설치)
pip install whls/agent_common-0.4.14-py3-none-any.whl
```

---

## 📋 버전 변경 이력 (Changelog)

자세한 버전 변경 이력은 [CHANGELOG.md](CHANGELOG.md) 파일을 참고하세요.
