# 1.2. 不変ドット記法参照およびランタイム保護 (ReadOnlyConfig)

> **所属モジュール**: `agent_common.config_loader.ReadOnlyConfig`, `agent_common.config_loader.ConfigLoader`  
> **関連グローバルインスタンス**: `from agent_common.config_loader import config`

---

## 1. 概要および設計意図

従来の Python 辞書ベースの設定値参照（`config['ecs']['endpoint_url']`）は、以下のような深刻な保守性および安定性の問題を引き起こします:
1. **キーの誤字・脱字に脆弱**: 文字列キーのタイポ（Typo）はコンパイル時や静的解析で検出できません。
2. **コード可読性の低下**: ネストされた角括弧とクォーテーションの多用により視覚的ノイズが増加します。
3. **ランタイム改変のリスク**: 任意のモジュールやスレッドから `config['key'] = new_val` のように共有設定が変更され、他のコンポーネントの挙動を破壊する恐れがあります。

`ReadOnlyConfig` はこれらの問題を未然に防止するため、**ドット記法（Dot-notation、属性アクセス）と厳格な不変性（Immutability）**を融合した高性能設定ラッパークラスです。

---

## 2. 設定ファイル例 (`config/config.yml`)

`ReadOnlyConfig` は以下のような YAML ファイル構造をドット記法に 1:1 マッピングし、Python オブジェクトの属性のように自然にアクセスできるようにサポートします。

```yaml
# config/config.yml (プロジェクト設定ファイル例)
ecs:
  endpoint_url: "https://storage.example.com"
  bucket_name_str: "app-storage-bucket"
  max_retries_int: 3
  timeout_seconds_int: 30

gcs:
  bucket_name_str: "gcp-prod-data-lake"
  prefix_str: "raw_data/events"
  ecscopy_bool: true

bigquery:
  project_id: "company-data-platform"
  dataset_id: "enterprise_dw"
  table_id: "customer_activity_logs"

transfer:
  max_workers_int: 8
  is_active_bool: "true"  # 型保証により bool(True) に自動変換
  allowed_types_list:    # リスト構造保証
    - "json"
    - "parquet"
```

---

## 3. 主要機能および特徴

### 3.1. 直感的なドット記法 (Dot-Notation) ナビゲーション
`config.ecs.endpoint_url`, `config.transfer.max_workers_int` のように、オブジェクトのプロパティにアクセスする感覚で簡潔に設定値を読み取ることができます。

- ネストされた下位辞書（`dict`）は、参照時に自動的にもう一つの `ReadOnlyConfig` オブジェクトとして再帰ラッピングされます。
- ネストされたリスト（`list`）内の辞書要素も自動的に `ReadOnlyConfig` でラップされ、一貫した属性参照が保証されます。
- キー末尾の型サフィックス（`_int`, `_float`, `_bool`, `_str`, `_list`, `_dict`）に基づく自動型変換および型保証が適用されます。

### 3.2. 厳格な不変性 (Read-Only 保証)
設定オブジェクトの完全性を保証するため、すべての変更および削除操作を根本から遮断します:

```python
def __setattr__(self, key: str, value: Any) -> None:
    raise TypeError("config 設定値は実行時に変更できません (Read-Only)。")

def __setitem__(self, key: str, value: Any) -> None:
    raise TypeError("config 設定値は実行時に変更できません (Read-Only)。")

def __delattr__(self, key: str) -> None:
    raise TypeError("config 設定値は実行時に削除できません (Read-Only)。")

def __delitem__(self, key: str) -> None:
    raise TypeError("config 設定値は実行時に削除できません (Read-Only)。")
```

### 3.3. 既存の辞書インターフェースとの完全な互換性
ドット記法だけでなく、従来の Python 辞書構文との相互運用性も提供します:

- **インデックス参照**: `config['ecs']['endpoint_url']` (ドット記法と同一結果)
- **メンバーシップ検証 (`in` 演算子)**: `'ecs' in config`, `'endpoint_url' in config.ecs`
- **純粋な辞書への変換**: `config.to_dict()` を通じて外部ライブラリ（Boto3, BigQuery Client 等）に元データ辞書を安全に受け渡し可能

---

## 4. 実践コード例

### 4.1. グローバル `config` 基本参照パターン

```python
from agent_common.config_loader import config

# 1. ドット記法による階層アクセス (第2章の config.yml 基準)
endpoint_str: str = config.ecs.endpoint_url          # "https://storage.example.com"
bucket_str: str = config.gcs.bucket_name_str         # "gcp-prod-data-lake"
max_workers: int = config.transfer.max_workers_int    # 8 (int 型保証)
is_active: bool = config.transfer.is_active_bool     # True (bool 型保証)

# 2. 存在チェック (in 演算子)
if "bigquery" in config and "dataset_id" in config.bigquery:
    dataset_name = config.bigquery.dataset_id        # "enterprise_dw"

# 3. 外部 API 呼び出し用の生辞書抽出
ecs_kwargs: dict = config.ecs.to_dict()
```

### 4.2. 改変試行時の例外発生 (防御動作)

```python
from agent_common.config_loader import config

try:
    # 実行時のプロパティ改変試行
    config.ecs.endpoint_url = "http://malicious-url:9020"
except TypeError as e:
    print(f"改変防止成功: {e}")
    # 出力: 改変防止成功: config 設定値は実行時に変更できません (Read-Only)。

try:
    # 辞書インデックスによる変更試行
    config['ecs']['endpoint_url'] = "http://malicious-url:9020"
except TypeError as e:
    print(f"改変防止成功: {e}")
```

### 4.3. 未定義プロパティ参照時の Fail-Fast エラー出力

```python
from agent_common.config_loader import config

try:
    non_existent = config.ecs.unknown_property
except AttributeError as e:
    print(f"属性エラー: {e}")
    # 出力: 属性エラー: config.ymlに定義されていない設定項目です: 'unknown_property'
```

---

## 5. デフォルトパス以外の `config.yml` 設定方法

デフォルトでは、`from agent_common.config_loader import config` は**プロジェクトルートの `config/` ディレクトリ（`config/config.yml`）**を自動検知して読み込みます。

しかし、**環境別設定分離 (dev/staging/prod)**、**バッチ/テスト専用設定**、または**外部マウントボリュームパス**を参照させたい場合、以下の3通りの方法でカスタムパスを指定できます。

### 方法 1. `ConfigLoader` コンストラクタにカスタムパスを渡す (推奨)

`ConfigLoader(config_dir=...)` コンストラクタに相対パスまたは絶対パスを渡し、それを `ReadOnlyConfig` でラップすることで、該当パスの設定を参照する独立した不変設定オブジェクトを作成できます:

```python
from pathlib import Path
from agent_common.config_loader import ConfigLoader, ReadOnlyConfig

# 1) プロジェクトルート基準の相対パス指定 (例: environments/prod/config/)
prod_loader = ConfigLoader(config_dir="environments/prod/config")
prod_config = ReadOnlyConfig(prod_loader)

print(prod_config.ecs.endpoint_url)  # prod 設定ファイルの内容を参照

# 2) OS 絶対パス指定 (例: Docker コンテナマウントボリューム /etc/app/config/)
external_loader = ConfigLoader(config_dir=Path("/etc/app/config"))
external_config = ReadOnlyConfig(external_loader)

print(external_config.bigquery.project_id)
```

### 方法 2. `config_dir` プロパティ (Setter) による動的パス変更

既存の `ConfigLoader` インスタンスの設定ディレクトリを実行時に変更できます。`config_dir` プロパティを変更すると内部キャッシュが自動的に無効化され、新しいディレクトリの YAML ファイル群が即座に再読み込みされます:

```python
from agent_common.config_loader import ConfigLoader, ReadOnlyConfig

loader = ConfigLoader()

# プロパティ Setter による設定ディレクトリ変更 (内部キャッシュ自動無効化)
loader.config_dir = "custom_configs/batch_job"
# またはメソッド呼び出し: loader.config_dir_set("custom_configs/batch_job")

batch_config = ReadOnlyConfig(loader)
print(batch_config.transfer.max_workers_int)
```

### 方法 3. テストコード用インメモリ辞書の直接引き渡し

単体テスト（pytest）やモック（Mock）環境では、実際の YAML ファイルを配置することなく純粋な Python 辞書を直接 `ReadOnlyConfig` に渡すことで、全く同一のドット記法および不変性テストを実行できます:

```python
from agent_common.config_loader import ReadOnlyConfig

# 単体テスト用モック設定データ
mock_data = {
    "ecs": {
        "endpoint_url": "https://mock-storage.example.com",
        "timeout_seconds_int": 5
    },
    "transfer": {
        "max_workers_int": "2",  # _int 型自動保証適用
        "dry_run_bool": "true"    # _bool 型自動保証適用
    }
}

# 辞書から直接 ReadOnlyConfig を生成
test_config = ReadOnlyConfig(mock_data)

# 本番コードと同一のドット記法および型保証を利用
assert test_config.ecs.endpoint_url == "https://mock-storage.example.com"
assert test_config.transfer.max_workers_int == 2       # int 保証
assert test_config.transfer.dry_run_bool is True       # bool 保証
```

---

## 6. ベストプラクティス設計規則 (AGENTS.md 連携)

- **規則 1.4.2 (Direct Immutable Config Access)**:  
  静的で不変なグローバル設定値をクラス内部の `self` インスタンス変数に冗長コピー（Clone）しないでください。  
  必ず `config.ecs.endpoint_url` のようにグローバル `config` オブジェクトを直接参照し、信頼できる唯一の情報源（Single Source of Truth）を維持してください。
- **マルチ環境の分離**:  
  バッチスクリプトや複数環境の同時実行においてグローバル設定を汚染しないよう、`ConfigLoader(config_dir="...")` を介して明示的に専用の設定インスタンスを分離生成してください。
