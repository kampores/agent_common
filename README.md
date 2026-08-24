# agent_common 패키지

중앙 에이전트 및 데이터 이관/생성 서비스를 위한 공통 로깅, 설정 로더, 인프라 클라이언트, 동적 도구(Tool) 파서 및 에러 처리 라이브러리 패키지입니다.

---

## 📌 주요 제공 기능

### 1. 설정 로더 (`agent_common.config_loader`)
- 계층적 YAML 설정 파싱 및 병합 (Deep Merge)
- 패키지 내 기본 설정(`agent_common/config/*.yml`)과 개별 프로젝트 설정 오버라이드 지원
- `setting("key.path")` 형태의 점 표기법 설정 조회 기능 및 `NO_PROXY` 환경변수 자동 반영
- `ensure_config_file()`: 프로젝트 기본 설정 템플릿 자동 생성 및 검증 지원

### 2. 단일 행 로깅 포매터 및 로거 (`agent_common.logger`)
- `SingleLineFlattenFormatter`: 모든 로그 및 Traceback 예외 메시지를 1줄로 평탄화하여 중앙 로그 수집(Logstash, Fluentd 등)에 최적화
- `ProjectLogger`: 콘솔 및 파일 로그 핸들러 동적 생성 및 일자별 로그 분리 관리
- `logging_messages.yml` 사전 기반 한글 포맷 템플릿 연동 로깅 지원

### 3. 스토리지 및 데이터베이스 클라이언트 (`agent_common.clients`)
- `EcsClient`: Dell ECS S3 저장소 접속, 목록 조회, 메타데이터 파싱 및 파일 메모리 스트리밍 획득
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
- `ProgressTracker`: 멀티스레드 실시간 진행률 추적(`[N/Total] (P%)`), 처리 속도 및 남은 시간 예측, 10% 단위 마일스톤 경고 승격 로깅, 최종 요약 리포트(Summary Report) 생성
- `DateTimeUtils`: 전역 일시 헬퍼 함수군

### 6. 공용 에러 및 예외 핸들러 (`agent_common.error_handler`)
- 네트워크 장애, 설정 오류, 런타임 예외에 대한 일관된 로깅 및 핸들링 제공

---

## 🛠️ 사용 예시 (Usage Examples)

### 1. ToolParser를 통한 동적 룰 평가
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

### 2. ProgressTracker 실시간 진행률 추적
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
pip install whls/agent_common-0.4.1-py3-none-any.whl
```

---

## 📋 버전 변경 이력 (Changelog)

자세한 버전 변경 이력은 [CHANGELOG.md](CHANGELOG.md) 파일을 참고하세요.
