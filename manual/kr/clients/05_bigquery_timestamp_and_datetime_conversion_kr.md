# 3.5. BigQuery TIMESTAMP·DATETIME 일시 문자열 변환

> **소속 모듈**: `agent_common.clients.BigQueryClient`  
> **핵심 메서드**: `convert_to_bigquery_timestamp()`, `convert_to_bigquery_datetime()`  
> **관련 설정**: `config.bigquery.timezone_offset_str`

---

## 1. 개요

원천 시스템이 내보내는 일시 값은 `20260824153000`, `2026/08/24 15:30`, `2026-08-24T15:30:00Z`처럼 형식이 제각각입니다. `BigQueryClient`는 이런 값을 BigQuery가 받아들이는 표준 문자열로 정규화하는 두 메서드를 제공합니다.

- `convert_to_bigquery_timestamp()`: `TIMESTAMP` 컬럼용. 타임존 오프셋이 붙은 문자열을 반환합니다.
- `convert_to_bigquery_datetime()`: `DATETIME` 컬럼용. 오프셋이 없는 문자열을 반환합니다.

---

## 2. 컬럼 타입별 선택 기준

| 컬럼 타입 | 의미 | 사용할 메서드 | 반환 예 |
| :--- | :--- | :--- | :--- |
| `TIMESTAMP` | 시간대와 무관한 절대 시점. BigQuery 콘솔에는 UTC로 표시됩니다. | `convert_to_bigquery_timestamp()` | `2026-08-24 15:30:00+09:00` |
| `DATETIME` | 시간대 정보가 없는 벽시계 시각. 저장한 숫자가 그대로 표시됩니다. | `convert_to_bigquery_datetime()` | `2026-08-24 15:30:00` |

콘솔이나 BI 도구에서 현지 시각 숫자가 변환 없이 그대로 보여야 한다면 `DATETIME` 컬럼을 사용하세요. `TIMESTAMP` 컬럼은 조회할 때 `DATETIME(timestamp_col, 'Asia/Seoul')`처럼 시간대를 지정해 변환합니다.

---

## 3. 메서드 규격

### 3.1. TIMESTAMP 문자열 변환 (`convert_to_bigquery_timestamp`)
```python
def convert_to_bigquery_timestamp(
    self,
    val_any: Any,
    default_tz_offset_str: Optional[str] = None,
) -> Optional[str]
```
- **지원 입력 포맷**:
  - `ISO 8601` 형식 (`2026-08-24T15:30:00+09:00`, `2026-08-24 15:30:00Z` 등)
  - 공백/슬래시 구분 일시 (`2026/08/24 15:30:00`, `2026-08-24 15:30`)
  - 14자리 압축 일시 (`20260824153000`)
  - 8자리 일자 (`20260824` -> `2026-08-24 00:00:00`)
- **타임존 오프셋 결정 우선순위**:
  1. 원천 문자열 자체에 명시된 오프셋 (`Z`, `+09:00`, `-0500` 등). 값을 환산하지 않고 그대로 유지합니다.
  2. 파라미터 `default_tz_offset_str`
  3. 설정 파일 `config.bigquery.timezone_offset_str`
  4. 설정이 비어 있거나 `AUTO`/`SYSTEM`이면 호스트 시스템의 로컬 타임존 (`TimeUtils.get_system_timezone_offset_str()`)
- 값이 비어 있거나 날짜로 해석할 수 없으면 `None`을 반환합니다.

### 3.2. DATETIME 문자열 변환 (`convert_to_bigquery_datetime`)
```python
def convert_to_bigquery_datetime(self, val_any: Any) -> Optional[str]
```
- **지원 입력 포맷**: `convert_to_bigquery_timestamp`와 동일합니다.
- **타임존 처리**:
  - 원천 문자열에 오프셋(`Z`, `+09:00`, `-0500` 등)이 있으면 한국 시각(KST)으로 환산한 뒤 오프셋을 제거합니다.
  - 오프셋이 없으면 시각 숫자를 그대로 사용합니다.
  - `timezone_offset_str` 설정의 영향을 받지 않습니다.
- 값이 비어 있거나 날짜로 해석할 수 없으면 `None`을 반환합니다.

---

## 4. 사용 예시

### 4.1. TIMESTAMP 컬럼용 변환
`config.bigquery.timezone_offset_str`이 `"+09:00"`일 때의 결과입니다.
```python
from agent_common.clients import BigQueryClient

bq_client = BigQueryClient(
    project_id_str="my-project",
    dataset_id_str="analytics",
    table_id_str="tb_events",
)

# 1) 14자리 문자열 -> "2026-08-24 15:30:00+09:00"
ts_1 = bq_client.convert_to_bigquery_timestamp("20260824153000")

# 2) 8자리 일자 -> "2026-08-24 00:00:00+09:00"
ts_2 = bq_client.convert_to_bigquery_timestamp("20260824")

# 3) 오프셋이 명시된 ISO 8601 -> "2026-08-24 15:30:00Z" (오프셋 유지)
ts_3 = bq_client.convert_to_bigquery_timestamp("2026-08-24T15:30:00Z")

# 4) 호출 시 기본 오프셋 지정 -> "2026-08-24 15:30:00+00:00"
ts_4 = bq_client.convert_to_bigquery_timestamp("20260824153000", default_tz_offset_str="+00:00")
```

### 4.2. DATETIME 컬럼용 변환
```python
# bq_client는 4.1과 동일하게 생성합니다.

# 1) 14자리 문자열 -> "2026-08-24 15:30:00"
dt_1 = bq_client.convert_to_bigquery_datetime("20260824153000")

# 2) 오프셋이 없는 ISO 일시 -> "2026-08-24 15:30:00" (숫자 그대로)
dt_2 = bq_client.convert_to_bigquery_datetime("2026-08-24T15:30:00")

# 3) UTC 표기(Z) -> "2026-08-25 00:30:00" (KST로 환산)
dt_3 = bq_client.convert_to_bigquery_datetime("2026-08-24T15:30:00Z")

# 4) 해석할 수 없는 값 -> None
dt_4 = bq_client.convert_to_bigquery_datetime("abc")
```
