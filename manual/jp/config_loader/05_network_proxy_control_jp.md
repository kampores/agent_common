# 1.5. ネットワークプロキシ制御 (`_apply_no_proxy`)

> **所属モジュール**: `agent_common.config_loader.ConfigLoader`  
> **中核メソッド**: `ConfigLoader._apply_no_proxy(settings)`

---

## 1. 概要および企業システムにおける背景

企業の閉域網やハイブリッドクラウド環境では、外部インターネット通信（外部 LLM API の呼び出し等）のために全社アウトバウンドプロキシ（`HTTP_PROXY`, `HTTPS_PROXY`）の利用が義務付けられていることが一般的です。

しかし、社内プライベートネットワーク内に位置する **Dell ECS オブジェクトストレージ**、**オンプレミスデータベース**、あるいは **K8s/クラウド内部メタデータサーバー**への通信まで外部プロキシを経由してしまうと、以下のような深刻な障害が発生します:
1. 社内内部 IP/ドメインを外部プロキシサーバーが名前解決できず、`502 Bad Gateway` や `Connection Refused` が発生する。
2. 大容量オブジェクトデータ（GB〜TB 単位）がプロキシ機器を通過することで、ネットワークボトルネックや帯域枯渇を引き起こす。

`ConfigLoader` はこれらの問題を自動的に回避するため、設定ファイル（`config.yml`）に宣言された `proxy.no_proxy` リストを検知し、OS 環境変数 `NO_PROXY` へと**安全に自動注入・同期**します。

---

## 2. 動作メカニズム (`_apply_no_proxy`)

`ConfigLoader.get_settings()` が実行されるたびに、内部的に `_apply_no_proxy` が自動呼び出しされます:

```python
def _apply_no_proxy(self, settings: dict[str, Any]) -> None:
    """proxy.no_proxy 設定値を NO_PROXY 環境変数に適用する。"""
    no_proxy_value = settings.get("proxy", {}).get("no_proxy")
    if no_proxy_value:
        existing = os.environ.get("NO_PROXY", "")
        if existing:
            os.environ["NO_PROXY"] = f"{existing},{no_proxy_value}"
        else:
            os.environ["NO_PROXY"] = str(no_proxy_value)
```

### 主要な特徴:
1. **無損失累積マージ (Non-destructive Merge)**:
   - システムまたは上位コンテナ（Docker, Airflow Pod）に既に `NO_PROXY` 環境変数が定義されている場合、それを上書き消去せずカンマ（`,`）で安全に追記連結します。
2. **自動ライフサイクル反映**:
   - 個別の初期化コードを呼び出す必要はなく、`from agent_common.config_loader import config` を実行するだけでプロセス全体に即時適用されます。
3. **標準ライブラリとの連携**:
   - Python の `urllib.request`, `requests`, `boto3`, `google-cloud-storage` など主要なすべての HTTP/ネットワーククライアントライブラリが OS `NO_PROXY` 環境変数を標準認識するため、確実なプロキシバイパスが保証されます。

---

## 3. 設定ファイルの記述方法 (`config/config.yml`)

`config/config.yml` 内に以下のように `proxy` セクションを定義します:

```yaml
proxy:
  # 外部通信用プロキシ (必要に応じて指定)
  http_proxy: "http://proxy.example.com:8080"
  https_proxy: "http://proxy.example.com:8080"
  
  # プロキシを経由せず直接接続する内部ホスト/IP一覧 (カンマ区切り)
  no_proxy: "localhost,127.0.0.1,192.168.1.100,192.168.1.101,.internal.example.com"
```

---

## 4. 実践動作および検証例

```python
import os
from agent_common.config_loader import config

# 1. config ロード時に _apply_no_proxy が自動実行される
current_no_proxy = os.environ.get("NO_PROXY")
print(f"現在適用されている NO_PROXY: {current_no_proxy}")
# 出力: localhost,127.0.0.1,192.168.1.100,192.168.1.101,.internal.example.com

# 2. 内部ストレージ/API への直接通信
# 呼び出し時、OS NO_PROXY に登録された内部 IP/ホストはプロキシをバイパスし高速直接通信を実施
```

---

## 5. 運用ベストプラクティス

- **CIDR 表記の注意**: 一部の Python ライブラリ（`urllib` 等）は `192.168.0.0/16` 形式の CIDR 表記を完全サポートしていない場合があるため、明示的な IP プレフィックス（例: `.example.com`, `192.168.1.100`）で記載するのが最も安全です。
- **ローカルホストの必須含有**: `localhost,127.0.0.1` はシステムのループバック通信障害を防止するため、常に `no_proxy` リストの先頭に含めるようにしてください。
