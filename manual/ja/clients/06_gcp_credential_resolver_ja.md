# 3.6. GCP サービスアカウント認証リゾルバー (`GcpCredentialResolver`)

> **所属モジュール**: `agent_common.clients.GcpCredentialResolver` (`from agent_common import GcpCredentialResolver`)  
> **中核メソッド**: `resolve()`  
> **依存パッケージ**: `google-auth`

---

## 1. 概要

`GcpCredentialResolver` は、GCP サービスアカウントの認証オブジェクト（`google.auth.credentials.Credentials`）の解決だけを担当する独立クラスです。

`GcsClient` と `BigQueryClient` はこのクラスを継承せず、**コンポジション**で保持します（`self.credential_resolver`）。そのため、どちらか一方のクライアントだけを切り出しても他方に依存しません。また、`agent_common` がクライアントを提供していない他の GCP サービス（Pub/Sub、Secret Manager など）でも、同じ認証ルールをそのまま再利用できます。

---

## 2. 4段階の認証優先順位

`resolve()` は以下の順序で、最初に該当した方式を使用します。フロー図は [3.2. GcsClient マニュアル](02_gcs_cloud_storage_client_ja.md) を参照してください。

| 順位 | 認証ソース | 動作 |
| :---: | :--- | :--- |
| 1 | 環境変数 `GOOGLE_APPLICATION_CREDENTIALS_JSON` | キーファイルをディスクに置かず、環境変数の JSON 文字列から認証オブジェクトを生成 |
| 2 | 環境変数 `GOOGLE_APPLICATION_CREDENTIALS` | Google 公式の標準環境変数が指すキーファイル（`.json`）を読み込み |
| 3 | `credentials_path_str` | コンストラクタに渡したキーファイルパスを読み込み（通常は `config.yml` の設定値） |
| 4 | なし | `None` を返却し、各 GCP クライアントが ADC（Application Default Credentials）を使用 |

2位と3位のパスが相対パスの場合は、プロジェクトルート（`ConfigLoader.project_path`）を基準に補正されます。

---

## 3. 主要メソッド仕様

### 3.1. コンストラクタ (`__init__`)
```python
def __init__(self, credentials_path_str: str, config_loader_obj: ConfigLoader)
```
- `credentials_path_str`: サービスアカウントのキーファイルパス。指定しない場合は `""` を渡します。
- `config_loader_obj`: 相対パスをプロジェクトルート基準で補正する際に使用する `ConfigLoader` インスタンス。

### 3.2. 認証解決 (`resolve`)
```python
def resolve(self) -> Any
```
- 戻り値: `google.auth.credentials.Credentials` インスタンス。該当する認証ソースがない場合は `None`。
- `google.oauth2.service_account` モジュールは初回呼び出し時に一度だけ遅延読み込みされ、クラスにキャッシュされます。

---

## 4. 使用例

### 4.1. 他の GCP サービスで単独使用
```python
from google.cloud import pubsub_v1

from agent_common import ConfigLoader, GcpCredentialResolver

credential_resolver = GcpCredentialResolver(
    credentials_path_str="config/secrets/gcp_sa_key.json",
    config_loader_obj=ConfigLoader(),
)
credentials = credential_resolver.resolve()

# credentials が None の場合、Google クライアントは ADC を使用します。
publisher_client = pubsub_v1.PublisherClient(credentials=credentials)
```

### 4.2. 環境変数のみで認証（キーファイルなし）
```bash
export GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type": "service_account", "project_id": "my-project", ...}'
```

```python
from agent_common import ConfigLoader, GcpCredentialResolver

# パスを空にすると、環境変数 → ADC の順に解決します。
credentials = GcpCredentialResolver(credentials_path_str="", config_loader_obj=ConfigLoader()).resolve()
```

### 4.3. 独自の GCP クライアントクラスへ組み込む
`GcsClient`、`BigQueryClient` と同じ方式です。親クラスを持たないため、クラス単体で切り出しても動作します。
```python
from typing import Any

from google.cloud import secretmanager

from agent_common import ConfigLoader, GcpCredentialResolver


class SecretManagerClient:
    """Secret Manager の参照を担当するクライアントクラス。"""

    def __init__(self, credentials_path_str: str = ""):
        self.config_loader: ConfigLoader = ConfigLoader()
        self.credential_resolver: GcpCredentialResolver = GcpCredentialResolver(
            credentials_path_str=credentials_path_str,
            config_loader_obj=self.config_loader,
        )
        self.client: Any = secretmanager.SecretManagerServiceClient(
            credentials=self.credential_resolver.resolve()
        )
```

---

## 5. 例外処理ガイド

例外メッセージは韓国語で出力されます。下表は実際に出力される先頭の文言です。

| 発生例外 | 主な発生原因 | 対処方法 |
| :--- | :--- | :--- |
| `ImportError: ... 'google-auth' 패키지가 필요합니다` | `google-auth` が未インストール | `pip install agent_common[clients]` または `pip install google-auth` を実行 |
| `ValueError: GOOGLE_APPLICATION_CREDENTIALS_JSON 인메모리 JSON 인증 객체 생성에 실패했습니다` | 環境変数の JSON 構文エラー、または必須キーの欠落 | 環境変数に注入した JSON 文字列とエスケープ状態を確認 |
| `FileNotFoundError: 인증키 파일을 찾을 수 없습니다` | 2位または3位のパスにファイルが存在しない | メッセージに表示されたパスとソース（環境変数 / `config.yml`）を確認 |

`GcsClient`、`BigQueryClient` 経由で呼び出された場合、上記の例外は接続段階で `ConnectionError` にラップされて送出されます。元の例外は `__cause__` およびログのトレースバックで確認できます。
