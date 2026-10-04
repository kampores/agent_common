# 3.5. BigQuery TIMESTAMP 与 DATETIME 日期时间字符串转换

> **所属模块**: `agent_common.clients.BigQueryClient`  
> **核心方法**: `convert_to_bigquery_timestamp()`, `convert_to_bigquery_datetime()`  
> **关联配置**: `config.bigquery.timezone_offset_str`

---

## 1. 概述

源系统输出的日期时间值格式各不相同，例如 `20260824153000`、`2026/08/24 15:30`、`2026-08-24T15:30:00Z`。`BigQueryClient` 提供两个方法，将这些值规范化为 BigQuery 可接受的标准字符串。

- `convert_to_bigquery_timestamp()`: 用于 `TIMESTAMP` 列，返回带时区偏移量的字符串。
- `convert_to_bigquery_datetime()`: 用于 `DATETIME` 列，返回不带偏移量的字符串。

---

## 2. 按列类型选择方法

| 列类型 | 含义 | 使用的方法 | 返回示例 |
| :--- | :--- | :--- | :--- |
| `TIMESTAMP` | 与时区无关的绝对时间点。BigQuery 控制台以 UTC 显示。 | `convert_to_bigquery_timestamp()` | `2026-08-24 15:30:00+09:00` |
| `DATETIME` | 不含时区信息的钟表时刻。存入的数字原样显示。 | `convert_to_bigquery_datetime()` | `2026-08-24 15:30:00` |

如果需要在控制台或 BI 工具中不经转换地原样显示本地时间数字，请使用 `DATETIME` 列。`TIMESTAMP` 列则在查询时指定时区进行转换，例如 `DATETIME(timestamp_col, 'Asia/Seoul')`。

---

## 3. 方法规格

### 3.1. TIMESTAMP 字符串转换 (`convert_to_bigquery_timestamp`)
```python
def convert_to_bigquery_timestamp(
    self,
    val_any: Any,
    default_tz_offset_str: Optional[str] = None,
) -> Optional[str]
```
- **支持的输入格式**:
  - `ISO 8601` 格式（`2026-08-24T15:30:00+09:00`、`2026-08-24 15:30:00Z` 等）
  - 空格/斜杠分隔的日期时间（`2026/08/24 15:30:00`、`2026-08-24 15:30`）
  - 14 位压缩日期时间（`20260824153000`）
  - 8 位日期（`20260824` -> `2026-08-24 00:00:00`）
- **时区偏移量的决定优先级**:
  1. 源字符串中自带的偏移量（`Z`、`+09:00`、`-0500` 等）。不做换算，原样保留。
  2. 参数 `default_tz_offset_str`
  3. 配置项 `config.bigquery.timezone_offset_str`
  4. 配置为空或为 `AUTO`/`SYSTEM` 时，使用宿主系统的本地时区（`TimeUtils.get_system_timezone_offset_str()`）
- 值为空或无法解析为日期时返回 `None`。

### 3.2. DATETIME 字符串转换 (`convert_to_bigquery_datetime`)
```python
def convert_to_bigquery_datetime(self, val_any: Any) -> Optional[str]
```
- **支持的输入格式**: 与 `convert_to_bigquery_timestamp` 相同。
- **时区处理**:
  - 源字符串带有偏移量（`Z`、`+09:00`、`-0500` 等）时，先换算为韩国时间 (KST)，再去掉偏移量。
  - 没有偏移量时，直接使用原有的时刻数字。
  - 不受 `timezone_offset_str` 配置的影响。
- 值为空或无法解析为日期时返回 `None`。

---

## 4. 使用示例

### 4.1. TIMESTAMP 列转换
以下为 `config.bigquery.timezone_offset_str` 设为 `"+09:00"` 时的结果。
```python
from agent_common.clients import BigQueryClient

bq_client = BigQueryClient(
    project_id_str="my-project",
    dataset_id_str="analytics",
    table_id_str="tb_events",
)

# 1) 14 位字符串 -> "2026-08-24 15:30:00+09:00"
ts_1 = bq_client.convert_to_bigquery_timestamp("20260824153000")

# 2) 8 位日期 -> "2026-08-24 00:00:00+09:00"
ts_2 = bq_client.convert_to_bigquery_timestamp("20260824")

# 3) 带偏移量的 ISO 8601 -> "2026-08-24 15:30:00Z"（保留偏移量）
ts_3 = bq_client.convert_to_bigquery_timestamp("2026-08-24T15:30:00Z")

# 4) 调用时指定默认偏移量 -> "2026-08-24 15:30:00+00:00"
ts_4 = bq_client.convert_to_bigquery_timestamp("20260824153000", default_tz_offset_str="+00:00")
```

### 4.2. DATETIME 列转换
```python
# bq_client 的创建方式与 4.1 相同。

# 1) 14 位字符串 -> "2026-08-24 15:30:00"
dt_1 = bq_client.convert_to_bigquery_datetime("20260824153000")

# 2) 不带偏移量的 ISO 日期时间 -> "2026-08-24 15:30:00"（数字保持不变）
dt_2 = bq_client.convert_to_bigquery_datetime("2026-08-24T15:30:00")

# 3) UTC 标记 (Z) -> "2026-08-25 00:30:00"（换算为 KST）
dt_3 = bq_client.convert_to_bigquery_datetime("2026-08-24T15:30:00Z")

# 4) 无法解析的值 -> None
dt_4 = bq_client.convert_to_bigquery_datetime("abc")
```
