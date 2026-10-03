# 1.3. 型サフィックス自動型変換および型保証 (Type Guarantee & Coercion)

> **所属モジュール**: `agent_common.config_loader` (`coerce_type_by_key_suffix`, `coerce_dict_by_key_suffix`, `ReadOnlyConfig`, `ConfigLoader`)  
> **導入バージョン**: `v0.4.14` (汎用関数昇格および複数設定対応: `v0.4.32`)  
> **中核関数/メソッド**:  
> - `coerce_type_by_key_suffix(key_str, val_any)` (単一キー・値の汎用変換関数)  
> - `coerce_dict_by_key_suffix(data_dict)` (ネストされた辞書/リストの一括再帰変換関数)  
> - `ReadOnlyConfig(data, source_name_str="config.yml")` (不変ドット記法ラッパー)

---

## 1. 概要および背景

YAML ファイル作成時のクォーテーション漏れ（`timeout: 30` vs `timeout: "30"`）や、環境変数注入時にすべての値が文字列（`"true"`, `"100"`）として注入される現象により、Python 実行環境では以下のようなバグが頻発します:

- `"30" + 10` 演算時の `TypeError: can only concatenate str to str`
- `"false"` という文字列が `if config.is_enabled:` 条件式で `True` と評価されてしまう致命的な誤作動

`agent_common` は AGENTS.md 基準の**明示的な型サフィックス命名規則**と連動し、設定キーの末尾サフィックスに応じて Python 標準データ型へと**実行時に自動型変換し、厳格に型を保証（Coercion & Guarantee）**します。

`v0.4.32` 以降は、`config.yml` だけでなく**任意の外部設定ファイル（`rule.yml`, `mapping.yml`, `db.yml` 等）**やインメモリ辞書（JSON, Dict）でも単独で即座に import して活用できるよう、**汎用公開関数（`coerce_type_by_key_suffix`, `coerce_dict_by_key_suffix`）**として提供されています。

---

## 2. サポートするサフィックスおよび自動型変換ルール

| 設定キーサフィックス | 返却保証型 | 型変換およびクレンジング動作 | 失敗時の動作 (Fail-Fast) | 入力例および変換結果 |
| :--- | :---: | :--- | :--- | :--- |
| `_int` | `int` | `int(val)` 自動変換 | **`ValueError` 発生 (Fail-Fast)**<br/>正しい整数型の入力を案内 | `"100"` ➔ `100`<br/>`"abc"` ➔ `ValueError` |
| `_float` | `float` | `float(val)` 自動変換 | **`ValueError` 発生 (Fail-Fast)**<br/>正しい数値型の入力を案内 | `"3.14"` ➔ `3.14`<br/>`"xyz"` ➔ `ValueError` |
| `_bool` | `bool` | 明示的ブール型判定<br/>(Python `bool` または大文字小文字不問の `"true"` ➔ `True`, `"false"` ➔ `False`<br/>※ 数値 `0`, `1` およびその他の文字列は非サポート) | **`ValueError` / `TypeError` 発生 (Fail-Fast)**<br/>True または False 形式の入力を案内 | `"True"` ➔ `True`<br/>`"false"` ➔ `False`<br/>`1`, `"0"`, `"hello"` ➔ エラー発生 (Fail-Fast) |
| `_str` | `str` | `str(val).strip()` で前後の空白を自動除去 | - | `"  prod  "` ➔ `"prod"`<br/>`1234` ➔ `"1234"` |
| `_list` | `list` | タプル、セット、単一要素を `list` として保証 | - | `("a", "b")` ➔ `["a", "b"]`<br/>`"only_one"` ➔ `["only_one"]` |
| `_dict` | `dict` / `ReadOnlyConfig` | 辞書構造の保証および `ReadOnlyConfig` ラッピング | **`TypeError` 発生 (Fail-Fast)**<br/>辞書マッピング構造の入力を案内 | `{}` ➔ `ReadOnlyConfig({})`<br/>`123` ➔ `TypeError` |

> ⚠️ **注釈**: 元の値が `None` の場合は型変換を試みず、安全に `None` をそのまま返却します。

---

## 3. 中核変換アルゴリズム

### 3.1. 単一キー・値変換 (`coerce_type_by_key_suffix`)

```python
from agent_common.error_handler import ErrorHandler


def coerce_type_by_key_suffix(key_str: str, val_any: Any) -> Any:
    if val_any is None:
        return None

    if key_str.endswith("_int"):
        try:
            return int(val_any)
        except Exception as err:
            ErrorHandler.raise_coercion_error(
                key_str=key_str,
                val_any=val_any,
                expected_type_str="整数型(int)",
                guide_msg_str="整数値で入力してください。",
                cause_exc=err,
            )

    if key_str.endswith("_float"):
        try:
            return float(val_any)
        except Exception as err:
            ErrorHandler.raise_coercion_error(
                key_str=key_str,
                val_any=val_any,
                expected_type_str="浮動小数点型(float)",
                guide_msg_str="正しい数値形式で入力してください。",
                cause_exc=err,
            )

    if key_str.endswith("_bool"):
        if isinstance(val_any, bool):
            return val_any
        if isinstance(val_any, str):
            clean_str = val_any.strip().lower()
            if clean_str == "true":
                return True
            if clean_str == "false":
                return False
            ErrorHandler.raise_coercion_error(
                key_str=key_str,
                val_any=val_any,
                expected_type_str="ブール値(bool)",
                guide_msg_str="True または False の値で入力してください。",
                exc_cls=ValueError,
            )
        ErrorHandler.raise_coercion_error(
            key_str=key_str,
            val_any=val_any,
            expected_type_str="ブール値(bool)",
            guide_msg_str="True または False の値で入力してください。",
            exc_cls=TypeError,
        )

    if key_str.endswith("_str"):
        return str(val_any).strip()

    if key_str.endswith("_list"):
        if isinstance(val_any, list):
            return val_any
        if isinstance(val_any, (tuple, set)):
            return list(val_any)
        return [val_any]

    if key_str.endswith("_dict"):
        if isinstance(val_any, dict):
            return val_any
        if hasattr(val_any, "to_dict") and callable(val_any.to_dict):
            return val_any.to_dict()
        ErrorHandler.raise_coercion_error(
            key_str=key_str,
            val_any=val_any,
            expected_type_str="辞書(dict)",
            guide_msg_str="辞書マッピング構造で入力してください。",
            exc_cls=TypeError,
        )

    return val_any
```

### 3.2. ネストされた辞書の一括再帰変換 (`coerce_dict_by_key_suffix`)

```python
def coerce_dict_by_key_suffix(data_dict: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data_dict, dict):
        return data_dict

    result_dict: dict[str, Any] = {}
    for key_str, val_any in data_dict.items():
        if isinstance(val_any, dict):
            result_dict[key_str] = coerce_dict_by_key_suffix(val_any)
        elif isinstance(val_any, list):
            result_dict[key_str] = [
                coerce_dict_by_key_suffix(item_any) if isinstance(item_any, dict) else item_any
                for item_any in val_any
            ]
        else:
            result_dict[key_str] = coerce_type_by_key_suffix(key_str, val_any)
    return result_dict
```

---

## 4. 適用領域

型保証は `agent_common` 全般の設定ローダーおよび任意の外部設定ファイルに一貫して適用されます:

1. **ドット記法 (`ReadOnlyConfig.__getattr__`)**:  
   `config.transfer.max_workers_int` ➔ `int` 返却
2. **単一パス参照 (`ConfigLoader.setting()`)**:  
   `loader.setting("transfer.max_workers_int")` ➔ `int` 返却
3. **Fail-Fast 必須参照 (`ConfigLoader.require_setting()`)**:  
   `loader.require_setting("transfer.max_workers_int")` ➔ `int` 返却
4. **外部設定ファイルおよび辞書の直接変換 (`coerce_type_by_key_suffix`, `coerce_dict_by_key_suffix`)**:  
   外部 YAML/JSON 設定パース後の単一値または辞書全体に即時適用可能
5. **任意の設定ファイルの `ReadOnlyConfig` ラッピング**:  
   `ReadOnlyConfig(custom_dict, source_name_str="rule.yml")` 形式でドット記法 + 不変性 + ファイル特化の診断例外を提供

---

## 5. 実践的な活用例

### 5.1. 基本 `config/config.yml` ドット記法での活用

```python
from agent_common.config_loader import config

# 1) _int 保証: 即座に算術演算が可能
batch_size: int = config.transfer.max_workers_int
total_capacity = batch_size * 10  # 160 (整数演算成功)

# 2) _bool 保証: 文字列ブール判定ミスを完全防止
if config.transfer.is_active_bool:
    print("サービスが有効化されています。")

# 3) _str 保証: 空白の混入がない正確な文字列比較
if config.transfer.environment_str == "staging":
    print("ステージング環境です。")

# 4) _list 保証: for-in ループで反復可能
for tag in config.transfer.target_tags_list:
    print(f"タグ: {tag}")
```

### 5.2. 他の設定ファイル (`rule.yml`, `mapping.yml` 等) への汎用適用

#### A. ネストされた辞書の一括クレンジング (`coerce_dict_by_key_suffix`)

```python
import yaml
from agent_common import coerce_dict_by_key_suffix

with open("config/rule.yml", "r", encoding="utf-8") as f:
    raw_rules = yaml.safe_load(f)

# ネストされたすべてのキー(_int, _bool, _str 等)の値が一括型変換された辞書を取得
clean_rules = coerce_dict_by_key_suffix(raw_rules)

assert isinstance(clean_rules["retry"]["max_attempts_int"], int)
assert isinstance(clean_rules["features"]["enable_cache_bool"], bool)
```

#### B. 任意の設定ファイルの不変ドット記法ラッピング (`ReadOnlyConfig`)

```python
import yaml
from agent_common import ReadOnlyConfig

with open("config/mapping.yml", "r", encoding="utf-8") as f:
    mapping_data = yaml.safe_load(f)

# ファイル名を指定して不変ドット記法オブジェクトを生成
mapping_cfg = ReadOnlyConfig(mapping_data, source_name_str="mapping.yml")

# ドット記法と型保証を同時にサポート
timeout_sec = mapping_cfg.timeout_float
print(f"タイムアウト: {timeout_sec}")

# 未定義キー参照時は正確なファイル名付きで AttributeError 発生
# AttributeError: mapping.ymlに定義されていない設定項目です: 'undefined_key'
```

#### C. 単一キー・値変換 (`coerce_type_by_key_suffix`)

```python
from agent_common import coerce_type_by_key_suffix

# 環境変数や CLI 引数、外部 API レスポンス値の単件変換
port = coerce_type_by_key_suffix("server_port_int", "8080")  # 8080 (int)
debug = coerce_type_by_key_suffix("is_debug_bool", "true")   # True (bool)
```

この規則により、開発者は `int()`, `float()`, `.strip()` のような冗長な防御コードをビジネスロジックから完全に排除できます。
