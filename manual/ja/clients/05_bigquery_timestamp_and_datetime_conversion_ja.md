# 3.5. BigQuery TIMESTAMP・DATETIME 日時文字列変換

> **所属モジュール**: `agent_common.clients.BigQueryClient`  
> **中核メソッド**: `convert_to_bigquery_timestamp()`, `convert_to_bigquery_datetime()`  
> **関連設定**: `config.bigquery.timezone_offset_str`, `config.bigquery.datetime_timezone_str`

---

## 1. 概要

ソースシステムが出力する日時の値は、`20260824153000`、`2026/08/24 15:30`、`2026-08-24T15:30:00Z` のように形式がばらばらです。`BigQueryClient` は、これらの値を BigQuery が受け付ける標準文字列へ正規化する 2 つのメソッドを提供します。

- `convert_to_bigquery_timestamp()`: `TIMESTAMP` 列向け。タイムゾーンオフセット付きの文字列を返します。
- `convert_to_bigquery_datetime()`: `DATETIME` 列向け。オフセットなしの文字列を返します。

---

## 2. 列の型ごとの選択基準

| 列の型 | 意味 | 使用するメソッド | 戻り値の例 |
| :--- | :--- | :--- | :--- |
| `TIMESTAMP` | タイムゾーンに依存しない絶対時点。BigQuery コンソールでは UTC で表示されます。 | `convert_to_bigquery_timestamp()` | `2026-08-24 15:30:00+09:00` |
| `DATETIME` | タイムゾーン情報を持たない壁時計時刻。保存した数字がそのまま表示されます。 | `convert_to_bigquery_datetime()` | `2026-08-24 15:30:00` |

コンソールや BI ツールで現地時刻の数字を変換なしにそのまま表示したい場合は、`DATETIME` 列を使用してください。`TIMESTAMP` 列は、照会時に `DATETIME(timestamp_col, 'Asia/Seoul')` のようにタイムゾーンを指定して変換します。

---

## 3. メソッド仕様

### 3.1. TIMESTAMP 文字列変換 (`convert_to_bigquery_timestamp`)
```python
def convert_to_bigquery_timestamp(
    self,
    val_any: Any,
    default_tz_offset_str: Optional[str] = None,
) -> Optional[str]
```
- **対応入力フォーマット**:
  - `ISO 8601` 形式（`2026-08-24T15:30:00+09:00`、`2026-08-24 15:30:00Z` など）
  - 空白/スラッシュ区切りの日時（`2026/08/24 15:30:00`、`2026-08-24 15:30`）
  - 14桁の圧縮日時（`20260824153000`）
  - 8桁の日付（`20260824` -> `2026-08-24 00:00:00`）
- **タイムゾーンオフセットの決定優先順位**:
  1. 元の文字列に明記されたオフセット（`Z`、`+09:00`、`-0500` など）。換算せず、そのまま保持します。
  2. 引数 `default_tz_offset_str`
  3. 設定 `config.bigquery.timezone_offset_str`
  4. 設定が空、または `AUTO`/`SYSTEM` の場合は、ホストシステムのローカルタイムゾーン（`TimeUtils.get_system_timezone_offset_str()`）
- 値が空、または日付として解釈できない場合は `None` を返します。

### 3.2. DATETIME 文字列変換 (`convert_to_bigquery_datetime`)
```python
def convert_to_bigquery_datetime(self, val_any: Any) -> Optional[str]
```
- **対応入力フォーマット**: `convert_to_bigquery_timestamp` と同じです。
- **タイムゾーン処理**:
  - 元の文字列にオフセット（`Z`、`+09:00`、`-0500` など）がある場合、`config.bigquery.datetime_timezone_str`（既定値 `KST`）の時刻に換算してからオフセットを除去します。システム時刻が UTC の環境で生成した現在時刻（`DateTimeUtils.get_now_timestamp()`）も、このタイムゾーンの時刻で記録されます。
  - オフセットがない場合は、時刻の数字をそのまま使用します。
  - `datetime_timezone_str` には `KST` などのタイムゾーン略称、または `+09:00` 形式のオフセットを指定します。`AUTO`/`SYSTEM` の場合はホストシステムのローカルタイムゾーンを使用し、形式が不正な場合は `BigQueryClient` の生成時に `ValueError` が発生します。
  - `timezone_offset_str` 設定の影響は受けません。
- 値が空、または日付として解釈できない場合は `None` を返します。

---

## 4. 使用例

### 4.1. TIMESTAMP 列向け変換
`config.bigquery.timezone_offset_str` が `"+09:00"` の場合の結果です。
```python
from agent_common.clients import BigQueryClient

bq_client = BigQueryClient(
    project_id_str="my-project",
    dataset_id_str="analytics",
    table_id_str="tb_events",
)

# 1) 14桁文字列 -> "2026-08-24 15:30:00+09:00"
ts_1 = bq_client.convert_to_bigquery_timestamp("20260824153000")

# 2) 8桁日付 -> "2026-08-24 00:00:00+09:00"
ts_2 = bq_client.convert_to_bigquery_timestamp("20260824")

# 3) オフセット付きの ISO 8601 -> "2026-08-24 15:30:00Z"（オフセットを保持）
ts_3 = bq_client.convert_to_bigquery_timestamp("2026-08-24T15:30:00Z")

# 4) 呼び出し時にデフォルトオフセットを指定 -> "2026-08-24 15:30:00+00:00"
ts_4 = bq_client.convert_to_bigquery_timestamp("20260824153000", default_tz_offset_str="+00:00")
```

### 4.2. DATETIME 列向け変換
```python
# bq_client は 4.1 と同じ方法で生成します。

# 1) 14桁文字列 -> "2026-08-24 15:30:00"
dt_1 = bq_client.convert_to_bigquery_datetime("20260824153000")

# 2) オフセットなしの ISO 日時 -> "2026-08-24 15:30:00"（数字はそのまま）
dt_2 = bq_client.convert_to_bigquery_datetime("2026-08-24T15:30:00")

# 3) UTC 表記 (Z) -> "2026-08-25 00:30:00"（`datetime_timezone_str` の KST に換算）
dt_3 = bq_client.convert_to_bigquery_datetime("2026-08-24T15:30:00Z")

# 4) 解釈できない値 -> None
dt_4 = bq_client.convert_to_bigquery_datetime("abc")
```
