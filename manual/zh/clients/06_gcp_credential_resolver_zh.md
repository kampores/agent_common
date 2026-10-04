# 3.6. GCP 服务账号认证解析器 (`GcpCredentialResolver`)

> **所属模块**: `agent_common.clients.GcpCredentialResolver` (`from agent_common import GcpCredentialResolver`)  
> **核心方法**: `resolve()`  
> **依赖组件**: `google-auth`

---

## 1. 概述

`GcpCredentialResolver` 是一个独立类，只负责解析 GCP 服务账号认证对象 (`google.auth.credentials.Credentials`)。

`GcsClient` 与 `BigQueryClient` 并不继承它，而是通过**组合 (Composition)** 持有它 (`self.credential_resolver`)。因此单独拆分其中任一客户端时不依赖另一个客户端；对于 `agent_common` 未提供客户端的其他 GCP 服务（Pub/Sub、Secret Manager 等），也可以直接复用同一套认证规则。

---

## 2. 4 级认证优先级

`resolve()` 按以下顺序采用最先满足条件的方式。流程图请参阅 [3.2. GcsClient 手册](02_gcs_cloud_storage_client_zh.md)。

| 优先级 | 认证来源 | 行为 |
| :---: | :--- | :--- |
| 1 | 环境变量 `GOOGLE_APPLICATION_CREDENTIALS_JSON` | 不在磁盘保存密钥文件，直接由环境变量中的 JSON 字符串生成认证对象 |
| 2 | 环境变量 `GOOGLE_APPLICATION_CREDENTIALS` | 加载 Google 官方标准环境变量所指向的密钥文件 (`.json`) |
| 3 | `credentials_path_str` | 加载传入构造函数的密钥文件路径（通常为 `config.yml` 配置值） |
| 4 | 无 | 返回 `None`，由各 GCP 客户端使用 ADC (Application Default Credentials) |

第 2、3 级的路径若为相对路径，将以项目根目录 (`ConfigLoader.project_path`) 为基准进行修正。

---

## 3. 主要方法规格

### 3.1. 构造函数 (`__init__`)
```python
def __init__(self, credentials_path_str: str, config_loader_obj: ConfigLoader)
```
- `credentials_path_str`: 服务账号密钥文件路径。不指定时传入 `""`。
- `config_loader_obj`: 用于将相对路径按项目根目录修正的 `ConfigLoader` 实例。

### 3.2. 认证解析 (`resolve`)
```python
def resolve(self) -> Any
```
- 返回值: `google.auth.credentials.Credentials` 实例；若没有适用的认证来源则返回 `None`。
- `google.oauth2.service_account` 模块仅在首次调用时延迟加载一次，并缓存在类上。

---

## 4. 使用示例

### 4.1. 在其他 GCP 服务中单独使用
```python
from google.cloud import pubsub_v1

from agent_common import ConfigLoader, GcpCredentialResolver

credential_resolver = GcpCredentialResolver(
    credentials_path_str="config/secrets/gcp_sa_key.json",
    config_loader_obj=ConfigLoader(),
)
credentials = credential_resolver.resolve()

# credentials 为 None 时，Google 客户端将使用 ADC。
publisher_client = pubsub_v1.PublisherClient(credentials=credentials)
```

### 4.2. 仅通过环境变量认证（无密钥文件）
```bash
export GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type": "service_account", "project_id": "my-project", ...}'
```

```python
from agent_common import ConfigLoader, GcpCredentialResolver

# 路径留空时，按 环境变量 → ADC 的顺序解析。
credentials = GcpCredentialResolver(credentials_path_str="", config_loader_obj=ConfigLoader()).resolve()
```

### 4.3. 组合到自定义 GCP 客户端类中
与 `GcsClient`、`BigQueryClient` 的做法相同。由于没有父类，单独拆出该类也能正常工作。
```python
from typing import Any

from google.cloud import secretmanager

from agent_common import ConfigLoader, GcpCredentialResolver


class SecretManagerClient:
    """负责 Secret Manager 查询的客户端类。"""

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

## 5. 异常处理指南

异常消息以韩语输出，下表按实际输出的开头文字列出。

| 异常 | 主要原因 | 处理方法 |
| :--- | :--- | :--- |
| `ImportError: ... 'google-auth' 패키지가 필요합니다` | 未安装 `google-auth` | 执行 `pip install agent_common[clients]` 或 `pip install google-auth` |
| `ValueError: GOOGLE_APPLICATION_CREDENTIALS_JSON 인메모리 JSON 인증 객체 생성에 실패했습니다` | 环境变量中的 JSON 语法错误或缺少必需字段 | 检查注入环境变量的 JSON 字符串及其转义 |
| `FileNotFoundError: 인증키 파일을 찾을 수 없습니다` | 第 2 级或第 3 级路径下不存在文件 | 确认消息中显示的路径及来源（环境变量 / `config.yml`） |

通过 `GcsClient`、`BigQueryClient` 调用时，上述异常会在连接阶段被包装为 `ConnectionError` 抛出，原始异常可通过 `__cause__` 及日志中的堆栈信息查看。
