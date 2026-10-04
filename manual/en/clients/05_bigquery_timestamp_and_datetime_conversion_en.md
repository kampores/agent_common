# 3.5. BigQuery TIMESTAMP and DATETIME String Conversion

> **Module**: `agent_common.clients.BigQueryClient`  
> **Key Methods**: `convert_to_bigquery_timestamp()`, `convert_to_bigquery_datetime()`  
> **Configuration**: `config.bigquery.timezone_offset_str`

---

## 1. Overview

Source systems emit date and time values in many shapes, such as `20260824153000`, `2026/08/24 15:30`, or `2026-08-24T15:30:00Z`. `BigQueryClient` provides two methods that normalize these values into the standard strings BigQuery accepts.

- `convert_to_bigquery_timestamp()`: for `TIMESTAMP` columns. Returns a string with a time zone offset.
- `convert_to_bigquery_datetime()`: for `DATETIME` columns. Returns a string without an offset.

---

## 2. Choosing by Column Type

| Column type | Meaning | Method to use | Example result |
| :--- | :--- | :--- | :--- |
| `TIMESTAMP` | An absolute point in time, independent of time zone. The BigQuery console displays it in UTC. | `convert_to_bigquery_timestamp()` | `2026-08-24 15:30:00+09:00` |
| `DATETIME` | A wall-clock time with no time zone. The stored digits are displayed as they are. | `convert_to_bigquery_datetime()` | `2026-08-24 15:30:00` |

If local clock digits must appear unchanged in the console or in BI tools, use a `DATETIME` column. For a `TIMESTAMP` column, convert at query time by naming the time zone, for example `DATETIME(timestamp_col, 'Asia/Seoul')`.

---

## 3. Method Reference

### 3.1. TIMESTAMP String Conversion (`convert_to_bigquery_timestamp`)
```python
def convert_to_bigquery_timestamp(
    self,
    val_any: Any,
    default_tz_offset_str: Optional[str] = None,
) -> Optional[str]
```
- **Supported input formats**:
  - `ISO 8601` (`2026-08-24T15:30:00+09:00`, `2026-08-24 15:30:00Z`, etc.)
  - Space/slash-separated datetimes (`2026/08/24 15:30:00`, `2026-08-24 15:30`)
  - 14-digit compact datetimes (`20260824153000`)
  - 8-digit dates (`20260824` -> `2026-08-24 00:00:00`)
- **Time zone offset precedence**:
  1. An offset written in the source string (`Z`, `+09:00`, `-0500`, etc.). The value is kept as is, not converted.
  2. The `default_tz_offset_str` parameter
  3. The `config.bigquery.timezone_offset_str` setting
  4. The host system's local time zone (`TimeUtils.get_system_timezone_offset_str()`) when the setting is empty or `AUTO`/`SYSTEM`
- Returns `None` when the value is empty or cannot be parsed as a date.

### 3.2. DATETIME String Conversion (`convert_to_bigquery_datetime`)
```python
def convert_to_bigquery_datetime(self, val_any: Any) -> Optional[str]
```
- **Supported input formats**: Same as `convert_to_bigquery_timestamp`.
- **Time zone handling**:
  - If the source string carries an offset (`Z`, `+09:00`, `-0500`, etc.), it is converted to Korea Standard Time (KST) and the offset is then dropped.
  - If there is no offset, the clock digits are used as they are.
  - It is not affected by the `timezone_offset_str` setting.
- Returns `None` when the value is empty or cannot be parsed as a date.

---

## 4. Usage Examples

### 4.1. Conversion for TIMESTAMP Columns
Results shown are for `config.bigquery.timezone_offset_str` set to `"+09:00"`.
```python
from agent_common.clients import BigQueryClient

bq_client = BigQueryClient(
    project_id_str="my-project",
    dataset_id_str="analytics",
    table_id_str="tb_events",
)

# 1) 14-digit string -> "2026-08-24 15:30:00+09:00"
ts_1 = bq_client.convert_to_bigquery_timestamp("20260824153000")

# 2) 8-digit date -> "2026-08-24 00:00:00+09:00"
ts_2 = bq_client.convert_to_bigquery_timestamp("20260824")

# 3) ISO 8601 with an explicit offset -> "2026-08-24 15:30:00Z" (offset kept)
ts_3 = bq_client.convert_to_bigquery_timestamp("2026-08-24T15:30:00Z")

# 4) Default offset given at call time -> "2026-08-24 15:30:00+00:00"
ts_4 = bq_client.convert_to_bigquery_timestamp("20260824153000", default_tz_offset_str="+00:00")
```

### 4.2. Conversion for DATETIME Columns
```python
# Create bq_client as in 4.1.

# 1) 14-digit string -> "2026-08-24 15:30:00"
dt_1 = bq_client.convert_to_bigquery_datetime("20260824153000")

# 2) ISO datetime without an offset -> "2026-08-24 15:30:00" (digits kept as is)
dt_2 = bq_client.convert_to_bigquery_datetime("2026-08-24T15:30:00")

# 3) UTC notation (Z) -> "2026-08-25 00:30:00" (converted to KST)
dt_3 = bq_client.convert_to_bigquery_datetime("2026-08-24T15:30:00Z")

# 4) Unparseable value -> None
dt_4 = bq_client.convert_to_bigquery_datetime("abc")
```
