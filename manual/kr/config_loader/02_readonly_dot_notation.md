# 1.2. 불변 점 표기법 조회 및 런타임 보호 (ReadOnlyConfig)

> **소속 모듈**: `agent_common.config_loader.ReadOnlyConfig`, `agent_common.config_loader.ConfigLoader`  
> **관련 전역 인스턴스**: `from agent_common.config_loader import config`

---

## 1. 개요 및 설계 의도

기존 파이썬 딕셔너리 기반 설정 조회(`config['ecs']['endpoint_url']`)는 다음과 같은 심각한 유지보수 및 안정성 문제를 야기합니다:
1. **키 오타에 취약**: 문자열 키 오타 시 컴파일 타임 및 정적 분석에서 감지 불가
2. **코드 가독성 저하**: 중첩 대괄호와 따옴표로 인한 시각적 피로도 증가
3. **런타임 변조 위험**: 임의의 모듈이나 스레드에서 `config['key'] = new_val` 형태로 공유 설정을 수정하여 다른 컴포넌트의 동작을 훼손할 가능성

`ReadOnlyConfig`는 이러한 문제를 원천 차단하기 위해 **점 표기법(Dot-notation, 속성 접근)과 엄격한 불변성(Immutability)**을 결합한 고성능 설정 래퍼 클래스입니다.

---

## 2. 예제 설정 파일 (`config/config.yml`)

`ReadOnlyConfig`는 아래와 같은 YAML 파일 구조를 점 표기법으로 1:1 매핑하여 파이썬 객체 속성처럼 자연스럽게 조회할 수 있도록 지원합니다.

```yaml
# config/config.yml (예제 프로젝트 설정 파일)
ecs:
  endpoint_url: "http://10.200.10.10:9020"
  bucket_name_str: "pak-unstr-prod"
  max_retries_int: 3
  timeout_seconds_int: 30

gcs:
  bucket_name_str: "gcp-prod-data-lake"
  prefix_str: "raw_data/pak"
  ecscopy_bool: true

bigquery:
  project_id: "company-data-platform"
  dataset_id: "enterprise_dw"
  table_id: "customer_activity_logs"

transfer:
  max_workers_int: 8
  is_active_bool: "yes"  # 타입 보증에 의해 bool(True)로 자동 변환
  allowed_types_list:    # 리스트 구조 보증
    - "json"
    - "parquet"
```

---

## 3. 주요 기능 및 특징

### 3.1. 직관적인 점 표기법(Dot-Notation) 탐색
`config.ecs.endpoint_url`, `config.transfer.max_workers_int`처럼 객체 속성에 접근하듯 간결하게 설정값을 읽어들일 수 있습니다.

- 중첩된 하위 딕셔너리(`dict`)는 읽기 시점에 자동으로 또 다른 `ReadOnlyConfig` 객체로 재귀 래핑됩니다.
- 중첩 리스트(`list`) 내의 딕셔너리 항목 또한 자동으로 `ReadOnlyConfig`로 래핑되어 일관된 속성 조회를 보장합니다.
- 키 접미사(`_int`, `_float`, `_bool`, `_str`, `_list`, `_dict`)에 따른 자동 형 변환 및 타입 보증이 함께 적용됩니다.

### 3.2. 엄격한 불변성 (Read-Only 보장)
설정 객체의 무결성을 보장하기 위해 모든 변경 및 삭제 연산을 원천 차단합니다:

```python
def __setattr__(self, key: str, value: Any) -> None:
    raise TypeError("config 설정값은 런타임에 수정할 수 없습니다 (Read-Only).")

def __setitem__(self, key: str, value: Any) -> None:
    raise TypeError("config 설정값은 런타임에 수정할 수 없습니다 (Read-Only).")

def __delattr__(self, key: str) -> None:
    raise TypeError("config 설정값은 런타임에 삭제할 수 없습니다 (Read-Only).")

def __delitem__(self, key: str) -> None:
    raise TypeError("config 설정값은 런타임에 삭제할 수 없습니다 (Read-Only).")
```

### 3.3. 기존 딕셔너리 인터페이스와의 완벽한 호환성
점 표기법뿐만 아니라 기존 파이썬 문법과의 상호 운용성을 완벽히 지원합니다:

- **인덱싱 조회**: `config['ecs']['endpoint_url']` (점 표기법과 동일 결과)
- **멤버십 검사 (`in` 연산자)**: `'ecs' in config`, `'endpoint_url' in config.ecs`
- **순수 딕셔너리 변환**: `config.to_dict()`를 통해 외부 라이브러리(Boto3, BigQuery Client 등)에 원본 딕셔너리 전달 가능

---

## 4. 실전 코드 예시

### 4.1. 전역 `config` 기본 조회 패턴

```python
from agent_common.config_loader import config

# 1. 점 표기법 계층 접근 (2장의 config.yml 기준)
endpoint_str: str = config.ecs.endpoint_url          # "http://10.200.10.10:9020"
bucket_str: str = config.gcs.bucket_name_str         # "gcp-prod-data-lake"
max_workers: int = config.transfer.max_workers_int    # 8 (int 타입 보증)
is_active: bool = config.transfer.is_active_bool     # True (bool 타입 보증)

# 2. 존재 여부 확인 (in 연산자)
if "bigquery" in config and "dataset_id" in config.bigquery:
    dataset_name = config.bigquery.dataset_id        # "enterprise_dw"

# 3. 외부 API 호출을 위한 딕셔너리 추출
ecs_kwargs: dict = config.ecs.to_dict()
```

### 4.2. 변조 시도 시 예외 발생 (방어적 동작)

```python
from agent_common.config_loader import config

try:
    # 런타임 속성 변조 시도
    config.ecs.endpoint_url = "http://malicious-url:9020"
except TypeError as e:
    print(f"변조 방어 성공: {e}")
    # 출력: 변조 방어 성공: config 설정값은 런타임에 수정할 수 없습니다 (Read-Only).

try:
    # 딕셔너리 인덱싱을 통한 변경 시도
    config['ecs']['endpoint_url'] = "http://malicious-url:9020"
except TypeError as e:
    print(f"변조 방어 성공: {e}")
```

### 4.3. 미정의 속성 접근 시 Fail-Fast 에러 안내

```python
from agent_common.config_loader import config

try:
    non_existent = config.ecs.unknown_property
except AttributeError as e:
    print(f"속성 오류: {e}")
    # 출력: 속성 오류: config.yml에 정의되지 않은 설정 항목입니다: 'unknown_property'
```

---

## 5. 기본 경로 외 다른 경로의 `config.yml` 설정 방법

기본적으로 `from agent_common.config_loader import config`는 **프로젝트 루트의 `config/` 디렉터리(`config/config.yml`)**를 자동으로 감지하여 로드합니다.

하지만 **환경별 설정 분리(dev/staging/prod)**, **배치/테스트 전용 설정**, 또는 **외부 마운트 볼륨 경로**를 바라보게 하고 싶을 경우 다음과 같은 3가지 방법으로 사용자 정의 경로를 지정할 수 있습니다.

### 방법 1. `ConfigLoader` 생성자에 사용자 정의 경로 전달 (가장 권장)

`ConfigLoader(config_dir=...)` 생성자에 상대 경로 또는 절대 경로를 전달한 뒤 `ReadOnlyConfig`로 감싸면, 해당 경로의 설정을 바라보는 독립적인 불변 설정 객체를 생성할 수 있습니다:

```python
from pathlib import Path
from agent_common.config_loader import ConfigLoader, ReadOnlyConfig

# 1) 프로젝트 루트 기준 상대 경로 지정 (예: environments/prod/config/)
prod_loader = ConfigLoader(config_dir="environments/prod/config")
prod_config = ReadOnlyConfig(prod_loader)

print(prod_config.ecs.endpoint_url)  # prod 설정 파일 내용 조회

# 2) OS 절대 경로 지정 (예: Docker 컨테이너 마운트 볼륨 /etc/app/config/)
external_loader = ConfigLoader(config_dir=Path("/etc/app/config"))
external_config = ReadOnlyConfig(external_loader)

print(external_config.bigquery.project_id)
```

### 방법 2. `config_dir` 프로퍼티(Setter)를 통한 동적 경로 변경

기존 `ConfigLoader` 인스턴스의 설정 디렉토리를 런타임에 변경할 수 있습니다. `config_dir` 프로퍼티를 변경하면 내부 캐시가 자동으로 초기화되어 즉시 새로운 디렉터리의 YAML 파일들을 다시 로드합니다:

```python
from agent_common.config_loader import ConfigLoader, ReadOnlyConfig

loader = ConfigLoader()

# 프로퍼티 Setter로 설정 디렉토리 변경 (내부 캐시 자동 무효화)
loader.config_dir = "custom_configs/batch_job"
# 또는 메서드 호출: loader.config_dir_set("custom_configs/batch_job")

batch_config = ReadOnlyConfig(loader)
print(batch_config.transfer.max_workers_int)
```

### 방법 3. 테스트 코드용 인메모리 딕셔너리 직접 전달

단위 테스트(pytest)나 모의(Mock) 환경에서는 실제 YAML 파일 없이 순수 파이썬 딕셔너리를 직접 `ReadOnlyConfig`에 전달하여 완벽히 동일한 점 표기법 및 불변성 테스트를 수행할 수 있습니다:

```python
from agent_common.config_loader import ReadOnlyConfig

# 단위 테스트용 모의 설정 데이터
mock_data = {
    "ecs": {
        "endpoint_url": "http://mock-ecs:9020",
        "timeout_seconds_int": 5
    },
    "transfer": {
        "max_workers_int": "2",  # _int 타입 자동 보증 적용됨
        "dry_run_bool": "true"    # _bool 타입 자동 보증 적용됨
    }
}

# 딕셔너리로부터 직접 ReadOnlyConfig 생성
test_config = ReadOnlyConfig(mock_data)

# 프로덕션 코드와 동일한 점 표기법 및 타입 보증 사용
assert test_config.ecs.endpoint_url == "http://mock-ecs:9020"
assert test_config.transfer.max_workers_int == 2       # int 보증
assert test_config.transfer.dry_run_bool is True       # bool 보증
```

---

## 6. 모범 아키텍처 규칙 (AGENTS.md 연계)

- **규칙 1.4.2 (Direct Immutable Config Access)**:  
  정적이고 불변인 전역 설정값을 클래스 내부 `self` 인스턴스 변수로 중복 복사(Clone)하지 마십시오.  
  반드시 `config.ecs.endpoint_url` 형태로 전역 `config` 객체를 직접 참조하여 단일 진실 공급원(Single Source of Truth)을 유지하십시오.
- **다중 환경 격리**:  
  배치 스크립트나 다중 환경 실행 시 전역 설정을 오염시키지 말고, `ConfigLoader(config_dir="...")`를 통해 명시적인 전용 설정 인스턴스를 격리하여 생성하십시오.
